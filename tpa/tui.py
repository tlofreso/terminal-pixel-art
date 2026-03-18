"""Interactive TUI editor using curses."""
from __future__ import annotations
import curses
import sys
from typing import Optional
from .model import Sprite, Color, parse_color, Cel
from .drawing import draw_line, draw_rect, draw_ellipse, draw_circle, flood_fill
from .transform import flip_sprite_h, flip_sprite_v, rotate_sprite
from .fileio import save_tpa, load_tpa
from .render import _checkerboard
from .palette import PICO8, DB16

UPPER_HALF = "\u2580"

TOOLS = ["pencil", "line", "rect", "ellipse", "circle", "fill", "eraser", "eyedropper"]
TOOL_KEYS = {"b": "pencil", "l": "line", "u": "rect", "o": "ellipse",
             "c": "circle", "g": "fill", "e": "eraser", "i": "eyedropper"}


class Editor:
    def __init__(self, sprite: Sprite, filepath: str):
        self.sprite = sprite
        self.filepath = filepath
        self.tool = "pencil"
        self.fg_color = Color(255, 255, 255)
        self.bg_color = Color(0, 0, 0)
        self.zoom = max(1, min(4, 32 // max(sprite.width, sprite.height)))
        self.scroll_x = 0
        self.scroll_y = 0
        self.cursor_x = 0
        self.cursor_y = 0
        self.palette = list(sprite.palette) if sprite.palette else list(PICO8)
        self.palette_idx = 0
        self.undo_stack: list = []
        self.redo_stack: list = []
        self.modified = False
        self.message = ""
        self.show_grid = False
        self.drag_start = None  # (x, y) for line/rect/ellipse tools
        self.filled = False

    def push_undo(self):
        self.undo_stack.append(self.sprite.snapshot())
        self.redo_stack.clear()
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.sprite.snapshot())
            self.sprite = self.undo_stack.pop()
            self.message = "Undo"

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.sprite.snapshot())
            self.sprite = self.redo_stack.pop()
            self.message = "Redo"

    def save(self):
        save_tpa(self.sprite, self.filepath)
        self.modified = False
        self.message = f"Saved: {self.filepath}"

    def draw_canvas(self, stdscr, start_y: int, start_x: int, max_h: int, max_w: int):
        """Draw the sprite canvas on screen."""
        sprite = self.sprite
        z = self.zoom

        canvas_w = min(sprite.width * z, max_w - 2)
        canvas_h_chars = min((sprite.height * z + 1) // 2, max_h - 1)

        for char_row in range(canvas_h_chars):
            top_y_pixel = char_row * 2 + self.scroll_y
            bot_y_pixel = top_y_pixel + 1

            for char_col in range(canvas_w):
                x_pixel = char_col // z + self.scroll_x // z

                ty = top_y_pixel // z
                by = bot_y_pixel // z

                if x_pixel >= sprite.width or ty >= sprite.height:
                    continue

                top_color = sprite.flatten_pixel(x_pixel, ty)
                bot_color = sprite.flatten_pixel(x_pixel, by) if by < sprite.height else None

                # Handle transparency with checkerboard
                if top_color is None or top_color.a == 0:
                    top_color = _checkerboard(x_pixel, ty)
                elif top_color.a < 255:
                    top_color = top_color.blend_over(_checkerboard(x_pixel, ty))

                if bot_color is None or (bot_color is not None and bot_color.a == 0):
                    bot_color = _checkerboard(x_pixel, by) if by < sprite.height else Color(40, 40, 40)
                elif bot_color is not None and bot_color.a < 255:
                    bot_color = bot_color.blend_over(_checkerboard(x_pixel, by))

                if bot_color is None:
                    bot_color = Color(40, 40, 40)

                # Highlight cursor position
                is_cursor = (x_pixel == self.cursor_x and
                             (ty == self.cursor_y or by == self.cursor_y))

                screen_y = start_y + char_row
                screen_x = start_x + char_col

                if screen_y < max_h and screen_x < max_w:
                    try:
                        if is_cursor:
                            stdscr.addstr(screen_y, screen_x, "X",
                                          curses.color_pair(0) | curses.A_BOLD)
                        else:
                            pair = self._get_color_pair(stdscr, top_color, bot_color)
                            stdscr.addstr(screen_y, screen_x, UPPER_HALF, pair)
                    except curses.error:
                        pass

    def _get_color_pair(self, stdscr, fg: Color, bg: Color) -> int:
        """Get or create a curses color pair for fg/bg colors."""
        # Use direct color if terminal supports it
        if not hasattr(self, '_color_cache'):
            self._color_cache = {}
            self._next_pair = 1
            self._next_color = 16

        key = (fg.r, fg.g, fg.b, bg.r, bg.g, bg.b)
        if key in self._color_cache:
            return curses.color_pair(self._color_cache[key])

        if self._next_pair >= curses.COLOR_PAIRS - 1:
            return curses.color_pair(0)

        try:
            fg_id = self._next_color
            self._next_color += 1
            bg_id = self._next_color
            self._next_color += 1
            curses.init_color(fg_id, fg.r * 1000 // 255, fg.g * 1000 // 255, fg.b * 1000 // 255)
            curses.init_color(bg_id, bg.r * 1000 // 255, bg.g * 1000 // 255, bg.b * 1000 // 255)
            curses.init_pair(self._next_pair, fg_id, bg_id)
            self._color_cache[key] = self._next_pair
            pair_id = self._next_pair
            self._next_pair += 1
            return curses.color_pair(pair_id)
        except curses.error:
            return curses.color_pair(0)

    def draw_ui(self, stdscr):
        """Draw the complete UI."""
        stdscr.erase()
        max_h, max_w = stdscr.getmaxyx()

        # Title bar
        title = f" TPA: {self.filepath} {'[modified]' if self.modified else ''}"
        title = title[:max_w-1]
        try:
            stdscr.addstr(0, 0, title, curses.A_REVERSE)
            stdscr.addstr(0, len(title), " " * (max_w - len(title) - 1), curses.A_REVERSE)
        except curses.error:
            pass

        # Canvas area
        canvas_start_y = 2
        canvas_start_x = 2
        sidebar_w = 20
        canvas_max_w = max_w - sidebar_w - 2
        canvas_max_h = max_h - 5

        self.draw_canvas(stdscr, canvas_start_y, canvas_start_x, canvas_max_h, canvas_max_w)

        # Sidebar - Tool info
        sx = max_w - sidebar_w
        try:
            stdscr.addstr(2, sx, f"Tool: {self.tool}", curses.A_BOLD)
            stdscr.addstr(3, sx, f"Fill: {'on' if self.filled else 'off'}")
            stdscr.addstr(4, sx, f"Color: {self.fg_color.to_hex()}")
            stdscr.addstr(5, sx, f"Cursor: ({self.cursor_x},{self.cursor_y})")
            stdscr.addstr(6, sx, f"Zoom: {self.zoom}x")

            # Layer info
            stdscr.addstr(8, sx, "Layers:", curses.A_BOLD)
            for i, layer in enumerate(self.sprite.layers):
                if i + 9 >= max_h - 5:
                    break
                vis = "V" if layer.visible else "."
                active = ">" if i == self.sprite.active_layer else " "
                name = layer.name[:sidebar_w-6]
                stdscr.addstr(9 + i, sx, f"{active}{vis} {name}")

            # Frame info
            fi = 9 + len(self.sprite.layers) + 1
            if fi < max_h - 5:
                stdscr.addstr(fi, sx, f"Frame: {self.sprite.active_frame + 1}/{self.sprite.frame_count}", curses.A_BOLD)

        except curses.error:
            pass

        # Palette bar at bottom
        pal_y = max_h - 3
        if pal_y > 0:
            try:
                for i, color in enumerate(self.palette[:min(len(self.palette), max_w // 3)]):
                    px = i * 3
                    if px + 2 >= max_w:
                        break
                    marker = f"{i:2d} " if i == self.palette_idx else "   "
                    pair = self._get_color_pair(stdscr, color, color)
                    stdscr.addstr(pal_y, px, "   ", pair)
                    if i == self.palette_idx:
                        stdscr.addstr(pal_y + 1, px, f"^{i}", curses.A_BOLD)
            except curses.error:
                pass

        # Status bar
        status_y = max_h - 1
        frame_s = f"{self.sprite.active_frame + 1}/{self.sprite.frame_count}"
        layer_s = self.sprite.current_layer().name
        pixel = self.sprite.flatten_pixel(self.cursor_x, self.cursor_y)
        pixel_s = pixel.to_hex() if pixel else "transparent"
        status = f" ({self.cursor_x},{self.cursor_y}) | {pixel_s} | Layer: {layer_s} | Frame: {frame_s} | {self.message}"
        try:
            stdscr.addstr(status_y, 0, status[:max_w-1], curses.A_REVERSE)
            if len(status) < max_w:
                stdscr.addstr(status_y, len(status), " " * (max_w - len(status) - 1), curses.A_REVERSE)
        except curses.error:
            pass

        # Help hint
        help_y = max_h - 2
        help_text = " b:pencil l:line u:rect o:ellipse c:circle g:fill e:eraser i:pick | Space:draw Ctrl+S:save q:quit"
        try:
            stdscr.addstr(help_y, 0, help_text[:max_w-1])
        except curses.error:
            pass

        stdscr.refresh()

    def handle_input(self, stdscr) -> bool:
        """Handle input. Returns False to quit."""
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            return False

        if key == -1:
            return True

        # Tool selection
        if key < 256:
            ch = chr(key)
            if ch in TOOL_KEYS:
                self.tool = TOOL_KEYS[ch]
                self.message = f"Tool: {self.tool}"
                self.drag_start = None
                return True

        # Movement
        if key == curses.KEY_UP:
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == curses.KEY_DOWN:
            self.cursor_y = min(self.sprite.height - 1, self.cursor_y + 1)
        elif key == curses.KEY_LEFT:
            self.cursor_x = max(0, self.cursor_x - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_x = min(self.sprite.width - 1, self.cursor_x + 1)

        # Zoom
        elif key == ord("+") or key == ord("="):
            self.zoom = min(8, self.zoom + 1)
            self._color_cache = {}
            self._next_pair = 1
            self._next_color = 16
        elif key == ord("-"):
            self.zoom = max(1, self.zoom - 1)
            self._color_cache = {}
            self._next_pair = 1
            self._next_color = 16

        # Draw with space
        elif key == ord(" "):
            self._apply_tool()

        # Enter confirms shape tools
        elif key == ord("\n") or key == curses.KEY_ENTER:
            if self.drag_start and self.tool in ("line", "rect", "ellipse", "circle"):
                self._finish_shape()
            else:
                self._apply_tool()

        # Escape cancels
        elif key == 27:
            self.drag_start = None
            self.message = "Cancelled"

        # Grid toggle
        elif key == ord("#"):
            self.show_grid = not self.show_grid

        # Fill toggle
        elif key == ord("f"):
            self.filled = not self.filled
            self.message = f"Fill: {'on' if self.filled else 'off'}"

        # Layer navigation
        elif key == ord("["):
            self.sprite.active_layer = max(0, self.sprite.active_layer - 1)
            self.message = f"Layer: {self.sprite.current_layer().name}"
        elif key == ord("]"):
            self.sprite.active_layer = min(len(self.sprite.layers) - 1, self.sprite.active_layer + 1)
            self.message = f"Layer: {self.sprite.current_layer().name}"

        # Frame navigation
        elif key == ord(",") or key == ord("<"):
            self.sprite.active_frame = max(0, self.sprite.active_frame - 1)
            self.message = f"Frame: {self.sprite.active_frame + 1}/{self.sprite.frame_count}"
        elif key == ord(".") or key == ord(">"):
            self.sprite.active_frame = min(self.sprite.frame_count - 1, self.sprite.active_frame + 1)
            self.message = f"Frame: {self.sprite.active_frame + 1}/{self.sprite.frame_count}"

        # Palette navigation
        elif key == ord("1"):
            self.palette_idx = max(0, self.palette_idx - 1)
            self.fg_color = self.palette[self.palette_idx]
            self.message = f"Color: {self.fg_color.to_hex()}"
        elif key == ord("2"):
            self.palette_idx = min(len(self.palette) - 1, self.palette_idx + 1)
            self.fg_color = self.palette[self.palette_idx]
            self.message = f"Color: {self.fg_color.to_hex()}"

        # Undo/Redo
        elif key == 26:  # Ctrl+Z
            self.undo()
        elif key == 25:  # Ctrl+Y
            self.redo()

        # Save
        elif key == 19:  # Ctrl+S
            self.save()

        # Add frame
        elif key == ord("n"):
            self.push_undo()
            self.sprite.add_frame(copy_from=self.sprite.active_frame)
            self.sprite.active_frame += 1
            self.modified = True
            self.message = f"Added frame {self.sprite.active_frame + 1}"

        # Add layer
        elif key == ord("N"):
            self.push_undo()
            name = f"Layer {len(self.sprite.layers)}"
            self.sprite.add_layer(name)
            self.sprite.active_layer = len(self.sprite.layers) - 1
            self.modified = True
            self.message = f"Added layer: {name}"

        # Toggle layer visibility
        elif key == ord("v"):
            layer = self.sprite.current_layer()
            layer.visible = not layer.visible
            self.message = f"Layer '{layer.name}': {'visible' if layer.visible else 'hidden'}"

        # Flip shortcuts
        elif key == ord("H"):
            self.push_undo()
            flip_sprite_h(self.sprite)
            self.modified = True
            self.message = "Flipped horizontally"
        elif key == ord("V"):
            self.push_undo()
            flip_sprite_v(self.sprite)
            self.modified = True
            self.message = "Flipped vertically"

        # Swap FG/BG
        elif key == ord("x"):
            self.fg_color, self.bg_color = self.bg_color, self.fg_color
            self.message = f"Swapped colors: FG={self.fg_color.to_hex()}"

        # Quit
        elif key == ord("q"):
            if self.modified:
                self.message = "Unsaved changes! Press Q again to quit or Ctrl+S to save"
                self.draw_ui(stdscr)
                k2 = stdscr.getch()
                if k2 == ord("q") or k2 == ord("Q"):
                    return False
                elif k2 == 19:  # Ctrl+S
                    self.save()
                return True
            return False

        return True

    def _apply_tool(self):
        """Apply current tool at cursor position."""
        x, y = self.cursor_x, self.cursor_y
        sprite = self.sprite

        if not sprite.in_bounds(x, y):
            return

        if self.tool == "pencil":
            self.push_undo()
            cel = sprite.current_cel()
            cel.set_pixel(x, y, self.fg_color)
            self.modified = True

        elif self.tool == "eraser":
            self.push_undo()
            cel = sprite.current_cel()
            cel.set_pixel(x, y, None)
            self.modified = True

        elif self.tool == "fill":
            self.push_undo()
            cel = sprite.current_cel()
            flood_fill(cel, x, y, self.fg_color, bounds=(sprite.width, sprite.height))
            self.modified = True
            self.message = f"Filled from ({x},{y})"

        elif self.tool == "eyedropper":
            pixel = sprite.flatten_pixel(x, y)
            if pixel:
                self.fg_color = pixel
                self.message = f"Picked: {pixel.to_hex()}"
            else:
                self.message = "Transparent pixel"

        elif self.tool in ("line", "rect", "ellipse", "circle"):
            if self.drag_start is None:
                self.drag_start = (x, y)
                self.message = f"Start: ({x},{y}) - move cursor and press Space/Enter to finish"
            else:
                self._finish_shape()

    def _finish_shape(self):
        """Complete a shape drawing operation."""
        if self.drag_start is None:
            return

        sx, sy = self.drag_start
        ex, ey = self.cursor_x, self.cursor_y
        self.push_undo()
        cel = self.sprite.current_cel()
        bounds = (self.sprite.width, self.sprite.height)

        if self.tool == "line":
            draw_line(cel, sx, sy, ex, ey, self.fg_color, bounds)
        elif self.tool == "rect":
            draw_rect(cel, sx, sy, ex, ey, self.fg_color, filled=self.filled, bounds=bounds)
        elif self.tool == "ellipse":
            draw_ellipse(cel, sx, sy, ex, ey, self.fg_color, filled=self.filled, bounds=bounds)
        elif self.tool == "circle":
            r = max(abs(ex - sx), abs(ey - sy))
            draw_circle(cel, sx, sy, r, self.fg_color, filled=self.filled, bounds=bounds)

        self.drag_start = None
        self.modified = True
        self.message = f"Drew {self.tool}"


def run_tui(sprite: Sprite, filepath: str):
    """Run the TUI editor."""
    def _main(stdscr):
        curses.start_color()
        curses.use_default_colors()
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)

        # Check color support
        if not curses.can_change_color():
            # Fallback: limited color mode
            pass

        editor = Editor(sprite, filepath)
        editor.message = "Welcome to TPA! Press 'q' to quit, Space to draw"

        while True:
            editor.draw_ui(stdscr)
            if not editor.handle_input(stdscr):
                break

    curses.wrapper(_main)
