"""File I/O: save/load .tpa (JSON), export PNG."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from .model import Sprite, Layer, Cel, Color, Tag


def sprite_to_dict(sprite: Sprite) -> dict:
    """Serialize sprite to a JSON-compatible dict."""
    layers = []
    for layer in sprite.layers:
        cels = {}
        for fi, cel in layer.cels.items():
            rows = []
            for row in cel.pixels:
                r = []
                for pixel in row:
                    r.append(pixel.to_hex() if pixel else None)
                rows.append(r)
            cels[str(fi)] = {
                "width": cel.width, "height": cel.height,
                "x_offset": cel.x_offset, "y_offset": cel.y_offset,
                "pixels": rows,
            }
        layers.append({
            "name": layer.name,
            "visible": layer.visible,
            "opacity": layer.opacity,
            "blend_mode": layer.blend_mode,
            "locked": layer.locked,
            "cels": cels,
        })

    tags = [{"name": t.name, "from": t.from_frame, "to": t.to_frame,
             "color": t.color, "direction": t.direction} for t in sprite.tags]

    palette = [c.to_hex() for c in sprite.palette]

    return {
        "version": 1,
        "name": sprite.name,
        "width": sprite.width,
        "height": sprite.height,
        "frame_count": sprite.frame_count,
        "frame_durations": sprite.frame_durations,
        "active_layer": sprite.active_layer,
        "active_frame": sprite.active_frame,
        "layers": layers,
        "tags": tags,
        "palette": palette,
    }


def dict_to_sprite(d: dict) -> Sprite:
    """Deserialize sprite from dict."""
    sprite = Sprite(
        width=d["width"], height=d["height"],
        frame_count=d["frame_count"],
        frame_durations=d.get("frame_durations", [100] * d["frame_count"]),
        active_layer=d.get("active_layer", 0),
        active_frame=d.get("active_frame", 0),
        name=d.get("name", ""),
    )

    for ld in d["layers"]:
        layer = Layer(
            name=ld["name"],
            visible=ld.get("visible", True),
            opacity=ld.get("opacity", 255),
            blend_mode=ld.get("blend_mode", "normal"),
            locked=ld.get("locked", False),
        )
        for fi_str, cd in ld["cels"].items():
            pixels = []
            for row in cd["pixels"]:
                pixels.append([Color.from_hex(p) if p else None for p in row])
            cel = Cel(
                width=cd["width"], height=cd["height"],
                pixels=pixels,
                x_offset=cd.get("x_offset", 0),
                y_offset=cd.get("y_offset", 0),
            )
            layer.cels[int(fi_str)] = cel
        sprite.layers.append(layer)

    for td in d.get("tags", []):
        sprite.tags.append(Tag(
            name=td["name"], from_frame=td["from"], to_frame=td["to"],
            color=td.get("color", "#6699cc"),
            direction=td.get("direction", "forward"),
        ))

    sprite.palette = [Color.from_hex(c) for c in d.get("palette", [])]
    return sprite


def save_tpa(sprite: Sprite, path: str):
    """Save sprite to .tpa JSON file."""
    data = sprite_to_dict(sprite)
    compact = sprite.width * sprite.height > 4096  # >64x64: skip indent
    with open(path, "w") as f:
        if compact:
            json.dump(data, f, separators=(",", ":"))
        else:
            json.dump(data, f, indent=2)


def load_tpa(path: str) -> Sprite:
    """Load sprite from .tpa JSON file."""
    with open(path) as f:
        data = json.load(f)
    return dict_to_sprite(data)


def export_png(sprite: Sprite, path: str, frame: Optional[int] = None,
               scale: int = 1):
    """Export sprite to PNG. Requires Pillow."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("PNG export requires Pillow: pip install Pillow")

    if frame is None:
        frame = sprite.active_frame

    img = Image.new("RGBA", (sprite.width * scale, sprite.height * scale), (0, 0, 0, 0))
    for y in range(sprite.height):
        for x in range(sprite.width):
            pixel = sprite.flatten_pixel(x, y, frame)
            if pixel:
                rgba = (pixel.r, pixel.g, pixel.b, pixel.a)
                for sy in range(scale):
                    for sx in range(scale):
                        img.putpixel((x * scale + sx, y * scale + sy), rgba)
    img.save(path)


def export_spritesheet(sprite: Sprite, path: str, columns: Optional[int] = None,
                       scale: int = 1, json_path: Optional[str] = None):
    """Export all frames as a spritesheet. Requires Pillow."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Spritesheet export requires Pillow: pip install Pillow")

    if columns is None:
        columns = sprite.frame_count
    rows = (sprite.frame_count + columns - 1) // columns

    sw = sprite.width * scale * columns
    sh = sprite.height * scale * rows
    sheet = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))

    frames_data = []
    for fi in range(sprite.frame_count):
        col = fi % columns
        row = fi // columns
        ox = col * sprite.width * scale
        oy = row * sprite.height * scale

        for y in range(sprite.height):
            for x in range(sprite.width):
                pixel = sprite.flatten_pixel(x, y, fi)
                if pixel:
                    rgba = (pixel.r, pixel.g, pixel.b, pixel.a)
                    for sy in range(scale):
                        for sx in range(scale):
                            sheet.putpixel((ox + x*scale + sx, oy + y*scale + sy), rgba)

        frames_data.append({
            "frame": fi,
            "x": ox, "y": oy,
            "w": sprite.width * scale, "h": sprite.height * scale,
            "duration": sprite.frame_durations[fi] if fi < len(sprite.frame_durations) else 100,
        })

    sheet.save(path)

    if json_path:
        meta = {
            "frames": frames_data,
            "meta": {
                "image": str(Path(path).name),
                "size": {"w": sw, "h": sh},
                "scale": scale,
                "frameTags": [
                    {"name": t.name, "from": t.from_frame, "to": t.to_frame,
                     "direction": t.direction}
                    for t in sprite.tags
                ],
            }
        }
        with open(json_path, "w") as f:
            json.dump(meta, f, indent=2)


def import_png(path: str, palette: Optional[list] = None) -> Sprite:
    """Import a PNG as a single-frame sprite. Requires Pillow."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("PNG import requires Pillow: pip install Pillow")

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    sprite = Sprite.new(w, h, name=Path(path).stem)
    cel = sprite.layers[0].cels[0]

    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            if a > 0:
                cel.pixels[y][x] = Color(r, g, b, a)

    return sprite
