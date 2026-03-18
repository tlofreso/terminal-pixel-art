"""Low-level drawing algorithms: line, rect, ellipse, flood fill."""
from __future__ import annotations
from typing import Optional, Callable, List, Tuple
from .model import Color, Cel


def set_pixel(cel: Cel, x: int, y: int, color: Optional[Color]):
    cel.set_pixel(x, y, color)


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Return list of (x, y) points on the line."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points


def draw_line(cel: Cel, x0: int, y0: int, x1: int, y1: int, color: Color,
              bounds: Tuple[int, int] = None):
    """Draw a line on the cel."""
    w, h = bounds or (cel.width, cel.height)
    for x, y in bresenham_line(x0, y0, x1, y1):
        if 0 <= x < w and 0 <= y < h:
            cel.set_pixel(x, y, color)


def draw_rect(cel: Cel, x0: int, y0: int, x1: int, y1: int, color: Color,
              filled: bool = False, bounds: Tuple[int, int] = None):
    """Draw a rectangle (outline or filled)."""
    w, h = bounds or (cel.width, cel.height)
    left, right = min(x0, x1), max(x0, x1)
    top, bottom = min(y0, y1), max(y0, y1)
    if filled:
        cl = max(left, 0)
        cr = min(right, w - 1)
        ct = max(top, 0)
        cb = min(bottom, h - 1)
        for y in range(ct, cb + 1):
            for x in range(cl, cr + 1):
                cel.pixels[y - cel.y_offset][x - cel.x_offset] = color
    else:
        for x in range(left, right + 1):
            if 0 <= top < h and 0 <= x < w:
                cel.set_pixel(x, top, color)
            if 0 <= bottom < h and 0 <= x < w:
                cel.set_pixel(x, bottom, color)
        for y in range(top + 1, bottom):
            if 0 <= left < w and 0 <= y < h:
                cel.set_pixel(left, y, color)
            if 0 <= right < w and 0 <= y < h:
                cel.set_pixel(right, y, color)


def draw_ellipse(cel: Cel, x0: int, y0: int, x1: int, y1: int, color: Color,
                 filled: bool = False, bounds: Tuple[int, int] = None):
    """Draw an ellipse using midpoint algorithm."""
    w, h = bounds or (cel.width, cel.height)
    # Center and radii
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    rx = abs(x1 - x0) / 2.0
    ry = abs(y1 - y0) / 2.0
    if rx < 0.5 or ry < 0.5:
        draw_line(cel, x0, y0, x1, y1, color, (w, h))
        return

    def plot4(px: int, py: int):
        points = [
            (int(cx + px), int(cy + py)),
            (int(cx - px), int(cy + py)),
            (int(cx + px), int(cy - py)),
            (int(cx - px), int(cy - py)),
        ]
        if filled:
            for y_val in [int(cy + py), int(cy - py)]:
                x_left = int(cx - px)
                x_right = int(cx + px)
                for x_val in range(x_left, x_right + 1):
                    if 0 <= x_val < w and 0 <= y_val < h:
                        cel.set_pixel(x_val, y_val, color)
        else:
            for px_, py_ in points:
                if 0 <= px_ < w and 0 <= py_ < h:
                    cel.set_pixel(px_, py_, color)

    # Midpoint ellipse algorithm
    x, y = 0, int(ry)
    rx2, ry2 = rx * rx, ry * ry
    p1 = ry2 - rx2 * ry + 0.25 * rx2

    dx = 0
    dy = 2 * rx2 * y

    while dx < dy:
        plot4(x, y)
        x += 1
        dx += 2 * ry2
        if p1 < 0:
            p1 += dx + ry2
        else:
            y -= 1
            dy -= 2 * rx2
            p1 += dx - dy + ry2

    p2 = ry2 * (x + 0.5) ** 2 + rx2 * (y - 1) ** 2 - rx2 * ry2
    while y >= 0:
        plot4(x, y)
        y -= 1
        dy -= 2 * rx2
        if p2 > 0:
            p2 += rx2 - dy
        else:
            x += 1
            dx += 2 * ry2
            p2 += dx - dy + rx2


def draw_circle(cel: Cel, cx: int, cy: int, radius: int, color: Color,
                filled: bool = False, bounds: Tuple[int, int] = None):
    """Draw a circle."""
    draw_ellipse(cel, cx - radius, cy - radius, cx + radius, cy + radius,
                 color, filled, bounds)


def flood_fill(cel: Cel, x: int, y: int, color: Color,
               tolerance: int = 0, bounds: Tuple[int, int] = None):
    """Flood fill starting from (x, y)."""
    w, h = bounds or (cel.width, cel.height)
    if not (0 <= x < w and 0 <= y < h):
        return
    target = cel.get_pixel(x, y)

    def colors_match(a: Optional[Color], b: Optional[Color]) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if tolerance == 0:
            return a == b
        return (abs(a.r - b.r) + abs(a.g - b.g) + abs(a.b - b.b) + abs(a.a - b.a)) <= tolerance * 4

    if colors_match(target, color):
        return

    visited = set()
    stack = [(x, y)]
    while stack:
        px, py = stack.pop()
        if (px, py) in visited:
            continue
        if not (0 <= px < w and 0 <= py < h):
            continue
        current = cel.get_pixel(px, py)
        if not colors_match(current, target):
            continue
        visited.add((px, py))
        cel.set_pixel(px, py, color)
        stack.extend([(px+1, py), (px-1, py), (px, py+1), (px, py-1)])
