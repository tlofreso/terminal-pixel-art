"""Transformations: flip, rotate, resize, crop, trim."""
from __future__ import annotations
from typing import Optional
from .model import Sprite, Cel, Color


def flip_cel_h(cel: Cel) -> Cel:
    """Flip cel horizontally."""
    new = Cel.empty(cel.width, cel.height)
    for y in range(cel.height):
        for x in range(cel.width):
            new.pixels[y][cel.width - 1 - x] = cel.pixels[y][x]
    return new


def flip_cel_v(cel: Cel) -> Cel:
    """Flip cel vertically."""
    new = Cel.empty(cel.width, cel.height)
    for y in range(cel.height):
        new.pixels[cel.height - 1 - y] = list(cel.pixels[y])
    return new


def rotate_cel_90(cel: Cel) -> Cel:
    """Rotate cel 90 degrees clockwise."""
    new = Cel.empty(cel.height, cel.width)
    for y in range(cel.height):
        for x in range(cel.width):
            new.pixels[x][cel.height - 1 - y] = cel.pixels[y][x]
    return new


def rotate_cel_180(cel: Cel) -> Cel:
    return flip_cel_h(flip_cel_v(cel))


def rotate_cel_270(cel: Cel) -> Cel:
    """Rotate cel 270 degrees clockwise (90 CCW)."""
    new = Cel.empty(cel.height, cel.width)
    for y in range(cel.height):
        for x in range(cel.width):
            new.pixels[cel.width - 1 - x][y] = cel.pixels[y][x]
    return new


def resize_cel(cel: Cel, new_w: int, new_h: int) -> Cel:
    """Resize cel using nearest-neighbor interpolation."""
    new = Cel.empty(new_w, new_h)
    for y in range(new_h):
        for x in range(new_w):
            src_x = int(x * cel.width / new_w)
            src_y = int(y * cel.height / new_h)
            src_x = min(src_x, cel.width - 1)
            src_y = min(src_y, cel.height - 1)
            new.pixels[y][x] = cel.pixels[src_y][src_x]
    return new


def crop_cel(cel: Cel, x: int, y: int, w: int, h: int) -> Cel:
    """Crop cel to a rectangular region."""
    new = Cel.empty(w, h)
    for ny in range(h):
        for nx in range(w):
            sx, sy = x + nx, y + ny
            if 0 <= sx < cel.width and 0 <= sy < cel.height:
                new.pixels[ny][nx] = cel.pixels[sy][sx]
    return new


def _apply_to_cels(sprite: Sprite, func, layer_idx: Optional[int] = None,
                   frame_idx: Optional[int] = None, new_w: int = None, new_h: int = None):
    """Apply a cel transformation to specified or all cels."""
    layers = [sprite.layers[layer_idx]] if layer_idx is not None else sprite.layers
    for layer in layers:
        frames = [frame_idx] if frame_idx is not None else list(layer.cels.keys())
        for fi in frames:
            if fi in layer.cels:
                layer.cels[fi] = func(layer.cels[fi])
    if new_w is not None:
        sprite.width = new_w
    if new_h is not None:
        sprite.height = new_h


def flip_sprite_h(sprite: Sprite, layer: Optional[int] = None, frame: Optional[int] = None):
    _apply_to_cels(sprite, flip_cel_h, layer, frame)


def flip_sprite_v(sprite: Sprite, layer: Optional[int] = None, frame: Optional[int] = None):
    _apply_to_cels(sprite, flip_cel_v, layer, frame)


def rotate_sprite(sprite: Sprite, degrees: int, layer: Optional[int] = None,
                  frame: Optional[int] = None):
    degrees = degrees % 360
    if degrees == 90:
        func = rotate_cel_90
    elif degrees == 180:
        func = rotate_cel_180
    elif degrees == 270:
        func = rotate_cel_270
    else:
        raise ValueError(f"Rotation must be 90, 180, or 270 degrees, got {degrees}")

    if degrees in (90, 270):
        _apply_to_cels(sprite, func, layer, frame, new_w=sprite.height, new_h=sprite.width)
    else:
        _apply_to_cels(sprite, func, layer, frame)


def resize_sprite(sprite: Sprite, new_w: int, new_h: int):
    def resizer(cel):
        return resize_cel(cel, new_w, new_h)
    _apply_to_cels(sprite, resizer, new_w=new_w, new_h=new_h)


def crop_sprite(sprite: Sprite, x: int, y: int, w: int, h: int):
    def cropper(cel):
        return crop_cel(cel, x, y, w, h)
    _apply_to_cels(sprite, cropper, new_w=w, new_h=h)


def trim_sprite(sprite: Sprite):
    """Remove empty borders from sprite."""
    min_x, min_y = sprite.width, sprite.height
    max_x, max_y = 0, 0

    for frame in range(sprite.frame_count):
        for y in range(sprite.height):
            for x in range(sprite.width):
                pixel = sprite.flatten_pixel(x, y, frame)
                if pixel and pixel.a > 0:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

    if min_x > max_x:  # all empty
        return

    w = max_x - min_x + 1
    h = max_y - min_y + 1
    crop_sprite(sprite, min_x, min_y, w, h)
