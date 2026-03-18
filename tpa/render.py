"""Terminal rendering using Unicode half-blocks and ANSI 24-bit color."""
from __future__ import annotations
from typing import Optional, TextIO
import sys
from .model import Sprite, Color


# Checkerboard colors for transparent areas
CHECK_LIGHT = Color(204, 204, 204)
CHECK_DARK = Color(170, 170, 170)

UPPER_HALF = "\u2580"  # ▀
LOWER_HALF = "\u2584"  # ▄
FULL_BLOCK = "\u2588"  # █
RESET = "\033[0m"


def _fg(c: Color) -> str:
    return f"\033[38;2;{c.r};{c.g};{c.b}m"


def _bg(c: Color) -> str:
    return f"\033[48;2;{c.r};{c.g};{c.b}m"


def _checkerboard(x: int, y: int) -> Color:
    return CHECK_LIGHT if (x + y) % 2 == 0 else CHECK_DARK


def render_sprite(sprite: Sprite, frame: Optional[int] = None,
                  show_grid: bool = False, zoom: int = 1,
                  transparent_bg: bool = True) -> str:
    """Render a sprite to a string using Unicode half-blocks.

    Each terminal character represents 2 vertical pixels (top/bottom).
    Uses 24-bit ANSI color codes for true-color output.
    """
    if frame is None:
        frame = sprite.active_frame

    lines = []

    # Top border with column numbers
    if sprite.width <= 64:
        # Tens row
        header_tens = "  "
        for x in range(sprite.width * zoom):
            real_x = x // zoom
            if real_x % 5 == 0 and real_x >= 10:
                header_tens += str(real_x // 10)
            else:
                header_tens += " "
        lines.append(header_tens)
        # Ones row
        header_ones = "  "
        for x in range(sprite.width * zoom):
            real_x = x // zoom
            if real_x % 5 == 0:
                header_ones += str(real_x % 10)
            else:
                header_ones += " "
        lines.append(header_ones)

    for row_pair in range(0, sprite.height * zoom, 2):
        # Row label
        real_y = row_pair // zoom
        label = f"{real_y:2d}" if sprite.height <= 64 else ""
        line = label

        for col in range(sprite.width * zoom):
            real_x = col // zoom
            top_y = row_pair // zoom
            bot_y = (row_pair + 1) // zoom if row_pair + 1 < sprite.height * zoom else None

            top_pixel = sprite.flatten_pixel(real_x, top_y, frame)
            bot_pixel = sprite.flatten_pixel(real_x, bot_y, frame) if bot_y is not None and bot_y < sprite.height else None

            # Handle transparency
            if transparent_bg:
                if top_pixel is None or top_pixel.a == 0:
                    top_pixel = _checkerboard(real_x, top_y)
                elif top_pixel.a < 255:
                    top_pixel = top_pixel.blend_over(_checkerboard(real_x, top_y))

                if bot_pixel is None or (bot_pixel is not None and bot_pixel.a == 0):
                    if bot_y is not None:
                        bot_pixel = _checkerboard(real_x, bot_y)
                elif bot_pixel is not None and bot_pixel.a < 255:
                    bot_pixel = bot_pixel.blend_over(_checkerboard(real_x, bot_y))

            if top_pixel is None:
                top_pixel = Color(0, 0, 0, 0)
            if bot_pixel is None:
                bot_pixel = Color(0, 0, 0, 0)

            if show_grid and (real_x % 8 == 0 or real_y % 8 == 0):
                grid_color = Color(100, 100, 100)
                if real_x % 8 == 0:
                    top_pixel = grid_color
                    bot_pixel = grid_color

            # Use upper half block: foreground = top, background = bottom
            line += _fg(top_pixel) + _bg(bot_pixel) + UPPER_HALF

        line += RESET
        lines.append(line)

    return "\n".join(lines)


def render_to_file(sprite: Sprite, f: TextIO, frame: Optional[int] = None):
    """Write rendered sprite to a file/stream."""
    f.write(render_sprite(sprite, frame))
    f.write("\n")


def print_sprite(sprite: Sprite, frame: Optional[int] = None,
                 show_grid: bool = False, zoom: int = 1):
    """Print sprite to stdout."""
    print(render_sprite(sprite, frame, show_grid=show_grid, zoom=zoom))


def render_palette(colors: list, cols: int = 16) -> str:
    """Render a color palette as a grid of color swatches."""
    lines = []
    for i in range(0, len(colors), cols):
        row = colors[i:i+cols]
        line = ""
        for j, c in enumerate(row):
            idx = i + j
            line += _bg(c) + f" {idx:2d} " + RESET
        lines.append(line)
    return "\n".join(lines)


def render_ascii(sprite: Sprite, frame: Optional[int] = None, chars: str = " ░▒▓█") -> str:
    """Render sprite as ASCII art using brightness-mapped characters."""
    if frame is None:
        frame = sprite.active_frame
    lines = []
    for y in range(sprite.height):
        line = ""
        for x in range(sprite.width):
            pixel = sprite.flatten_pixel(x, y, frame)
            if pixel is None or pixel.a == 0:
                line += chars[0]
            else:
                brightness = (pixel.r + pixel.g + pixel.b) / (3 * 255)
                idx = int(brightness * (len(chars) - 1))
                line += chars[idx]
        lines.append(line)
    return "\n".join(lines)
