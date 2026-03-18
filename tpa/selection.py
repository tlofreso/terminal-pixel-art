"""Selection operations."""
from __future__ import annotations
from typing import Optional, Set, Tuple
from .model import Sprite, Cel, Color


class Selection:
    """A pixel mask representing selected areas."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.mask: Set[Tuple[int, int]] = set()

    def is_selected(self, x: int, y: int) -> bool:
        return (x, y) in self.mask

    def select(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.mask.add((x, y))

    def deselect(self, x: int, y: int):
        self.mask.discard((x, y))

    def clear(self):
        self.mask.clear()

    def select_all(self):
        for y in range(self.height):
            for x in range(self.width):
                self.mask.add((x, y))

    def invert(self):
        all_pixels = {(x, y) for y in range(self.height) for x in range(self.width)}
        self.mask = all_pixels - self.mask

    def select_rect(self, x0: int, y0: int, x1: int, y1: int, mode: str = "replace"):
        """Select a rectangular region. Mode: replace, add, subtract, intersect."""
        rect = set()
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    rect.add((x, y))

        if mode == "replace":
            self.mask = rect
        elif mode == "add":
            self.mask |= rect
        elif mode == "subtract":
            self.mask -= rect
        elif mode == "intersect":
            self.mask &= rect

    def select_by_color(self, sprite: Sprite, x: int, y: int,
                        tolerance: int = 0, contiguous: bool = True,
                        frame: Optional[int] = None):
        """Select pixels by color (magic wand)."""
        if frame is None:
            frame = sprite.active_frame

        target = sprite.flatten_pixel(x, y, frame)

        def matches(px: Optional[Color]) -> bool:
            if target is None and px is None:
                return True
            if target is None or px is None:
                return False
            if tolerance == 0:
                return target == px
            diff = abs(target.r - px.r) + abs(target.g - px.g) + abs(target.b - px.b) + abs(target.a - px.a)
            return diff <= tolerance * 4

        if contiguous:
            visited = set()
            stack = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited:
                    continue
                if not (0 <= cx < sprite.width and 0 <= cy < sprite.height):
                    continue
                pixel = sprite.flatten_pixel(cx, cy, frame)
                if not matches(pixel):
                    continue
                visited.add((cx, cy))
                self.mask.add((cx, cy))
                stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])
        else:
            for py in range(sprite.height):
                for px in range(sprite.width):
                    pixel = sprite.flatten_pixel(px, py, frame)
                    if matches(pixel):
                        self.mask.add((px, py))

    @property
    def bounds(self) -> Optional[Tuple[int, int, int, int]]:
        """Return (x, y, w, h) bounding box of selection, or None if empty."""
        if not self.mask:
            return None
        xs = [p[0] for p in self.mask]
        ys = [p[1] for p in self.mask]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        return (x0, y0, x1 - x0 + 1, y1 - y0 + 1)

    @property
    def empty(self) -> bool:
        return len(self.mask) == 0

    def copy_from(self, sprite: Sprite, frame: Optional[int] = None) -> Cel:
        """Copy selected pixels into a new cel."""
        if frame is None:
            frame = sprite.active_frame
        bounds = self.bounds
        if bounds is None:
            return Cel.empty(0, 0)
        x0, y0, w, h = bounds
        cel = Cel.empty(w, h)
        cel.x_offset = x0
        cel.y_offset = y0
        for px, py in self.mask:
            pixel = sprite.flatten_pixel(px, py, frame)
            if pixel:
                cel.pixels[py - y0][px - x0] = pixel
        return cel

    def delete_from(self, sprite: Sprite, frame: Optional[int] = None):
        """Delete selected pixels from active layer."""
        if frame is None:
            frame = sprite.active_frame
        cel = sprite.current_layer().ensure_cel(frame, sprite.width, sprite.height)
        for px, py in self.mask:
            cel.set_pixel(px, py, None)
