"""CLI interface for TPA - Terminal Pixel Art."""
from __future__ import annotations
import argparse
import sys
import json
from pathlib import Path
from .model import Sprite, Color, parse_color
from . import fileio, drawing, transform, render, palette as palette_mod, selection


def cmd_new(args):
    """Create a new sprite."""
    bg = parse_color(args.bg) if args.bg else None
    sprite = Sprite.new(args.width, args.height, bg_color=bg, name=args.name or "")
    if args.palette:
        sprite.palette = palette_mod.get_palette(args.palette)
    fileio.save_tpa(sprite, args.file)
    print(f"Created {args.width}x{args.height} sprite: {args.file}")


def cmd_view(args):
    """View sprite in terminal."""
    sprite = fileio.load_tpa(args.file)
    frame = args.frame if args.frame is not None else sprite.active_frame
    if args.ascii:
        print(render.render_ascii(sprite, frame))
    else:
        render.print_sprite(sprite, frame, show_grid=args.grid, zoom=args.zoom)
    if args.info:
        _print_info(sprite)


def cmd_info(args):
    """Show sprite information."""
    sprite = fileio.load_tpa(args.file)
    _print_info(sprite)


def _print_info(sprite: Sprite):
    print(f"Size: {sprite.width}x{sprite.height}")
    print(f"Frames: {sprite.frame_count}")
    print(f"Layers ({len(sprite.layers)}):")
    for i, layer in enumerate(sprite.layers):
        vis = "visible" if layer.visible else "hidden"
        lock = " locked" if layer.locked else ""
        active = " *" if i == sprite.active_layer else ""
        print(f"  [{i}] {layer.name} ({vis}, opacity={layer.opacity}{lock}){active}")
    if sprite.tags:
        print(f"Tags ({len(sprite.tags)}):")
        for t in sprite.tags:
            print(f"  {t.name}: frames {t.from_frame}-{t.to_frame} ({t.direction})")
    print(f"Frame durations: {sprite.frame_durations}")


def cmd_pixel(args):
    """Draw a single pixel or read pixel color."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame

    if args.color is None:
        # Read mode
        pixel = sprite.flatten_pixel(args.x, args.y)
        if pixel:
            print(pixel.to_hex())
        else:
            print("transparent")
        return

    color = parse_color(args.color)
    cel = sprite.current_cel()
    cel.set_pixel(args.x, args.y, color)
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        print(f"Set ({args.x},{args.y}) = {color.to_hex()}")


def cmd_line(args):
    """Draw a line."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    color = parse_color(args.color)
    cel = sprite.current_cel()
    drawing.draw_line(cel, args.x1, args.y1, args.x2, args.y2, color, (sprite.width, sprite.height))
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        print(f"Drew line ({args.x1},{args.y1})->({args.x2},{args.y2}) in {color.to_hex()}")


def cmd_rect(args):
    """Draw a rectangle."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    color = parse_color(args.color)
    cel = sprite.current_cel()
    drawing.draw_rect(cel, args.x1, args.y1, args.x2, args.y2, color,
                      filled=args.fill, bounds=(sprite.width, sprite.height))
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        kind = "filled rect" if args.fill else "rect"
        print(f"Drew {kind} ({args.x1},{args.y1})->({args.x2},{args.y2}) in {color.to_hex()}")


def cmd_ellipse(args):
    """Draw an ellipse."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    color = parse_color(args.color)
    cel = sprite.current_cel()
    drawing.draw_ellipse(cel, args.x1, args.y1, args.x2, args.y2, color,
                         filled=args.fill, bounds=(sprite.width, sprite.height))
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        kind = "filled ellipse" if args.fill else "ellipse"
        print(f"Drew {kind} ({args.x1},{args.y1})->({args.x2},{args.y2}) in {color.to_hex()}")


def cmd_circle(args):
    """Draw a circle."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    color = parse_color(args.color)
    cel = sprite.current_cel()
    drawing.draw_circle(cel, args.cx, args.cy, args.radius, color,
                        filled=args.fill, bounds=(sprite.width, sprite.height))
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        kind = "filled circle" if args.fill else "circle"
        print(f"Drew {kind} center=({args.cx},{args.cy}) r={args.radius} in {color.to_hex()}")


def cmd_fill(args):
    """Flood fill."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    color = parse_color(args.color)
    cel = sprite.current_cel()
    drawing.flood_fill(cel, args.x, args.y, color,
                       tolerance=args.tolerance, bounds=(sprite.width, sprite.height))
    fileio.save_tpa(sprite, args.file)
    if not args.quiet:
        print(f"Filled from ({args.x},{args.y}) with {color.to_hex()}")


def cmd_erase(args):
    """Erase pixels (set to transparent)."""
    sprite = fileio.load_tpa(args.file)
    if args.layer is not None:
        sprite.active_layer = args.layer
    if args.frame is not None:
        sprite.active_frame = args.frame
    cel = sprite.current_cel()

    if args.all:
        cel.clear()
        if not args.quiet:
            print("Cleared entire cel")
    elif args.rect:
        x0, y0, x1, y1 = args.rect
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                cel.set_pixel(x, y, None)
        if not args.quiet:
            print(f"Erased rect ({x0},{y0})->({x1},{y1})")
    else:
        cel.set_pixel(args.x, args.y, None)
        if not args.quiet:
            print(f"Erased ({args.x},{args.y})")

    fileio.save_tpa(sprite, args.file)


def cmd_layer(args):
    """Layer operations."""
    sprite = fileio.load_tpa(args.file)

    if args.action == "add":
        idx = sprite.add_layer(args.name, position=args.position)
        fileio.save_tpa(sprite, args.file)
        print(f"Added layer '{args.name}' at index {idx}")

    elif args.action == "remove":
        idx = _resolve_layer(sprite, args.target)
        name = sprite.layers[idx].name
        sprite.remove_layer(idx)
        fileio.save_tpa(sprite, args.file)
        print(f"Removed layer '{name}'")

    elif args.action == "list":
        for i, layer in enumerate(sprite.layers):
            vis = "V" if layer.visible else "."
            lock = "L" if layer.locked else "."
            active = "*" if i == sprite.active_layer else " "
            print(f" {active}[{i}] {vis}{lock} {layer.name} (opacity={layer.opacity})")

    elif args.action == "select":
        idx = _resolve_layer(sprite, args.target)
        sprite.active_layer = idx
        fileio.save_tpa(sprite, args.file)
        print(f"Active layer: [{idx}] {sprite.layers[idx].name}")

    elif args.action == "set":
        idx = _resolve_layer(sprite, args.target)
        layer = sprite.layers[idx]
        if args.name:
            layer.name = args.name
        if args.visible is not None:
            layer.visible = args.visible.lower() in ("true", "1", "yes")
        if args.opacity is not None:
            layer.opacity = max(0, min(255, args.opacity))
        if args.locked is not None:
            layer.locked = args.locked.lower() in ("true", "1", "yes")
        fileio.save_tpa(sprite, args.file)
        print(f"Updated layer [{idx}] {layer.name}")

    elif args.action == "move":
        idx = _resolve_layer(sprite, args.target)
        layer = sprite.layers.pop(idx)
        sprite.layers.insert(args.position, layer)
        sprite.active_layer = args.position
        fileio.save_tpa(sprite, args.file)
        print(f"Moved layer '{layer.name}' to position {args.position}")

    elif args.action == "duplicate":
        idx = _resolve_layer(sprite, args.target)
        src = sprite.layers[idx]
        import copy
        new_layer = copy.deepcopy(src)
        new_layer.name = f"{src.name} copy"
        sprite.layers.insert(idx + 1, new_layer)
        fileio.save_tpa(sprite, args.file)
        print(f"Duplicated layer '{src.name}'")

    elif args.action == "merge-down":
        idx = _resolve_layer(sprite, args.target)
        if idx <= 0:
            print("Error: cannot merge down bottom layer", file=sys.stderr)
            sys.exit(1)
        top = sprite.layers[idx]
        bot = sprite.layers[idx - 1]
        for fi in range(sprite.frame_count):
            top_cel = top.get_cel(fi)
            bot_cel = bot.ensure_cel(fi, sprite.width, sprite.height)
            if top_cel:
                for y in range(sprite.height):
                    for x in range(sprite.width):
                        tp = top_cel.get_pixel(x, y)
                        if tp:
                            bp = bot_cel.get_pixel(x, y)
                            if bp:
                                bot_cel.set_pixel(x, y, tp.blend_over(bp))
                            else:
                                bot_cel.set_pixel(x, y, tp)
        sprite.layers.pop(idx)
        if sprite.active_layer >= len(sprite.layers):
            sprite.active_layer = len(sprite.layers) - 1
        fileio.save_tpa(sprite, args.file)
        print(f"Merged '{top.name}' into '{bot.name}'")

    elif args.action == "flatten":
        new_layer = sprite.layers[0].__class__(name="Flattened")
        for fi in range(sprite.frame_count):
            cel = new_layer.ensure_cel(fi, sprite.width, sprite.height)
            for y in range(sprite.height):
                for x in range(sprite.width):
                    pixel = sprite.flatten_pixel(x, y, fi)
                    cel.set_pixel(x, y, pixel)
        sprite.layers = [new_layer]
        sprite.active_layer = 0
        fileio.save_tpa(sprite, args.file)
        print("Flattened all layers")


def _resolve_layer(sprite: Sprite, target: str) -> int:
    """Resolve layer name or index."""
    try:
        idx = int(target)
        if 0 <= idx < len(sprite.layers):
            return idx
    except (ValueError, TypeError):
        pass
    for i, layer in enumerate(sprite.layers):
        if layer.name == target:
            return i
    print(f"Error: layer '{target}' not found", file=sys.stderr)
    sys.exit(1)


def cmd_frame(args):
    """Frame operations."""
    sprite = fileio.load_tpa(args.file)

    if args.action == "add":
        copy_from = args.copy_from
        idx = sprite.add_frame(copy_from=copy_from, position=args.position)
        fileio.save_tpa(sprite, args.file)
        print(f"Added frame {idx} (total: {sprite.frame_count})")

    elif args.action == "remove":
        sprite.remove_frame(args.index)
        fileio.save_tpa(sprite, args.file)
        print(f"Removed frame {args.index} (total: {sprite.frame_count})")

    elif args.action == "list":
        for i in range(sprite.frame_count):
            active = "*" if i == sprite.active_frame else " "
            dur = sprite.frame_durations[i] if i < len(sprite.frame_durations) else 100
            print(f" {active}[{i}] duration={dur}ms")

    elif args.action == "select":
        sprite.active_frame = args.index
        fileio.save_tpa(sprite, args.file)
        print(f"Active frame: {args.index}")

    elif args.action == "set":
        if args.duration is not None:
            while len(sprite.frame_durations) <= args.index:
                sprite.frame_durations.append(100)
            sprite.frame_durations[args.index] = args.duration
        fileio.save_tpa(sprite, args.file)
        print(f"Updated frame {args.index}")

    elif args.action == "duplicate":
        idx = sprite.add_frame(copy_from=args.index, position=args.index + 1)
        fileio.save_tpa(sprite, args.file)
        print(f"Duplicated frame {args.index} -> {idx}")


def cmd_tag(args):
    """Tag operations."""
    sprite = fileio.load_tpa(args.file)
    from .model import Tag

    if args.action == "add":
        tag = Tag(name=args.name, from_frame=args.from_frame, to_frame=args.to_frame,
                  direction=args.direction or "forward")
        sprite.tags.append(tag)
        fileio.save_tpa(sprite, args.file)
        print(f"Added tag '{args.name}' (frames {args.from_frame}-{args.to_frame})")

    elif args.action == "remove":
        sprite.tags = [t for t in sprite.tags if t.name != args.name]
        fileio.save_tpa(sprite, args.file)
        print(f"Removed tag '{args.name}'")

    elif args.action == "list":
        if not sprite.tags:
            print("No tags")
        for t in sprite.tags:
            print(f"  {t.name}: frames {t.from_frame}-{t.to_frame} ({t.direction})")


def cmd_transform(args):
    """Transform operations."""
    sprite = fileio.load_tpa(args.file)
    layer = args.layer
    frame = args.frame

    if args.action == "flip-h":
        transform.flip_sprite_h(sprite, layer, frame)
        print("Flipped horizontally")
    elif args.action == "flip-v":
        transform.flip_sprite_v(sprite, layer, frame)
        print("Flipped vertically")
    elif args.action == "rotate":
        transform.rotate_sprite(sprite, args.degrees, layer, frame)
        print(f"Rotated {args.degrees}°")
    elif args.action == "resize":
        transform.resize_sprite(sprite, args.new_width, args.new_height)
        print(f"Resized to {args.new_width}x{args.new_height}")
    elif args.action == "crop":
        transform.crop_sprite(sprite, args.x, args.y, args.w, args.h)
        print(f"Cropped to {args.w}x{args.h} at ({args.x},{args.y})")
    elif args.action == "trim":
        transform.trim_sprite(sprite)
        print(f"Trimmed to {sprite.width}x{sprite.height}")

    fileio.save_tpa(sprite, args.file)


def cmd_palette_cmd(args):
    """Palette operations."""
    sprite = fileio.load_tpa(args.file)

    if args.action == "show":
        if sprite.palette:
            print(render.render_palette(sprite.palette))
        else:
            print("No palette set. Use 'tpa palette <file> set <name>' to load one.")
            print(f"Available: {', '.join(palette_mod.PALETTES.keys())}")

    elif args.action == "set":
        sprite.palette = palette_mod.get_palette(args.name)
        fileio.save_tpa(sprite, args.file)
        print(f"Set palette to '{args.name}' ({len(sprite.palette)} colors)")

    elif args.action == "list":
        for name in palette_mod.PALETTES:
            print(f"  {name} ({len(palette_mod.PALETTES[name])} colors)")

    elif args.action == "add":
        color = parse_color(args.color)
        sprite.palette.append(color)
        fileio.save_tpa(sprite, args.file)
        print(f"Added {color.to_hex()} to palette (index {len(sprite.palette) - 1})")


def cmd_export(args):
    """Export sprite."""
    sprite = fileio.load_tpa(args.file)
    output = args.output

    if output.endswith(".png"):
        if args.spritesheet:
            json_out = output.replace(".png", ".json") if args.json else None
            fileio.export_spritesheet(sprite, output, columns=args.columns,
                                     scale=args.scale, json_path=json_out)
            print(f"Exported spritesheet: {output}")
            if json_out:
                print(f"Exported metadata: {json_out}")
        else:
            frame = args.frame if args.frame is not None else sprite.active_frame
            fileio.export_png(sprite, output, frame=frame, scale=args.scale)
            print(f"Exported frame {frame}: {output}")
    elif output.endswith(".tpa"):
        fileio.save_tpa(sprite, output)
        print(f"Saved: {output}")
    else:
        print(f"Unsupported format: {output}", file=sys.stderr)
        sys.exit(1)


def cmd_import(args):
    """Import image as sprite."""
    sprite = fileio.import_png(args.input)
    fileio.save_tpa(sprite, args.output)
    print(f"Imported {args.input} -> {args.output} ({sprite.width}x{sprite.height})")


def cmd_batch(args):
    """Execute batch commands from JSON."""
    sprite = fileio.load_tpa(args.file)
    data = json.loads(sys.stdin.read()) if args.input == "-" else json.loads(Path(args.input).read_text())

    for cmd in data.get("commands", []):
        op = cmd["op"]
        if op == "pixel":
            color = parse_color(cmd["color"])
            cel = sprite.current_cel()
            cel.set_pixel(cmd["x"], cmd["y"], color)
        elif op == "line":
            color = parse_color(cmd["color"])
            cel = sprite.current_cel()
            drawing.draw_line(cel, cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"],
                              color, (sprite.width, sprite.height))
        elif op == "rect":
            color = parse_color(cmd["color"])
            cel = sprite.current_cel()
            drawing.draw_rect(cel, cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"],
                              color, filled=cmd.get("fill", False),
                              bounds=(sprite.width, sprite.height))
        elif op == "ellipse":
            color = parse_color(cmd["color"])
            cel = sprite.current_cel()
            drawing.draw_ellipse(cel, cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"],
                                 color, filled=cmd.get("fill", False),
                                 bounds=(sprite.width, sprite.height))
        elif op == "fill":
            color = parse_color(cmd["color"])
            cel = sprite.current_cel()
            drawing.flood_fill(cel, cmd["x"], cmd["y"], color,
                               bounds=(sprite.width, sprite.height))
        elif op == "layer_select":
            sprite.active_layer = cmd["index"]
        elif op == "frame_select":
            sprite.active_frame = cmd["index"]
        elif op == "frame_add":
            sprite.add_frame(copy_from=cmd.get("copy_from"))
        elif op == "layer_add":
            sprite.add_layer(cmd["name"])

    fileio.save_tpa(sprite, args.file)
    print(f"Executed {len(data.get('commands', []))} commands")


def cmd_edit(args):
    """Launch interactive TUI editor."""
    from .tui import run_tui
    sprite = fileio.load_tpa(args.file) if Path(args.file).exists() else Sprite.new(
        args.width or 16, args.height or 16, name=Path(args.file).stem)
    run_tui(sprite, args.file)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tpa", description="Terminal Pixel Art - Aseprite for the terminal")
    sub = p.add_subparsers(dest="command", help="Command")

    # new
    s = sub.add_parser("new", help="Create a new sprite")
    s.add_argument("file", help="Output .tpa file")
    s.add_argument("width", type=int, help="Width in pixels")
    s.add_argument("height", type=int, help="Height in pixels")
    s.add_argument("--bg", help="Background color (hex or name)")
    s.add_argument("--name", help="Sprite name")
    s.add_argument("--palette", help="Initial palette preset")

    # view
    s = sub.add_parser("view", help="View sprite in terminal")
    s.add_argument("file", help=".tpa file")
    s.add_argument("--frame", "-f", type=int, help="Frame index")
    s.add_argument("--zoom", "-z", type=int, default=1, help="Zoom level")
    s.add_argument("--grid", "-g", action="store_true", help="Show grid")
    s.add_argument("--ascii", action="store_true", help="ASCII art mode")
    s.add_argument("--info", "-i", action="store_true", help="Also show info")

    # info
    s = sub.add_parser("info", help="Show sprite info")
    s.add_argument("file", help=".tpa file")

    # pixel
    s = sub.add_parser("pixel", help="Draw/read a pixel")
    s.add_argument("file", help=".tpa file")
    s.add_argument("x", type=int)
    s.add_argument("y", type=int)
    s.add_argument("color", nargs="?", help="Color (omit to read)")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # line
    s = sub.add_parser("line", help="Draw a line")
    s.add_argument("file")
    s.add_argument("x1", type=int)
    s.add_argument("y1", type=int)
    s.add_argument("x2", type=int)
    s.add_argument("y2", type=int)
    s.add_argument("color")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # rect
    s = sub.add_parser("rect", help="Draw a rectangle")
    s.add_argument("file")
    s.add_argument("x1", type=int)
    s.add_argument("y1", type=int)
    s.add_argument("x2", type=int)
    s.add_argument("y2", type=int)
    s.add_argument("color")
    s.add_argument("--fill", action="store_true")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # ellipse
    s = sub.add_parser("ellipse", help="Draw an ellipse")
    s.add_argument("file")
    s.add_argument("x1", type=int)
    s.add_argument("y1", type=int)
    s.add_argument("x2", type=int)
    s.add_argument("y2", type=int)
    s.add_argument("color")
    s.add_argument("--fill", action="store_true")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # circle
    s = sub.add_parser("circle", help="Draw a circle")
    s.add_argument("file")
    s.add_argument("cx", type=int)
    s.add_argument("cy", type=int)
    s.add_argument("radius", type=int)
    s.add_argument("color")
    s.add_argument("--fill", action="store_true")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # fill
    s = sub.add_parser("fill", help="Flood fill")
    s.add_argument("file")
    s.add_argument("x", type=int)
    s.add_argument("y", type=int)
    s.add_argument("color")
    s.add_argument("--tolerance", "-t", type=int, default=0)
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # erase
    s = sub.add_parser("erase", help="Erase pixels")
    s.add_argument("file")
    s.add_argument("x", type=int, nargs="?")
    s.add_argument("y", type=int, nargs="?")
    s.add_argument("--rect", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    s.add_argument("--all", action="store_true")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--quiet", "-q", action="store_true")

    # layer
    s = sub.add_parser("layer", help="Layer operations")
    s.add_argument("file")
    layer_sub = s.add_subparsers(dest="action")

    ls = layer_sub.add_parser("add")
    ls.add_argument("name")
    ls.add_argument("--position", type=int)

    ls = layer_sub.add_parser("remove")
    ls.add_argument("target", help="Layer index or name")

    layer_sub.add_parser("list")

    ls = layer_sub.add_parser("select")
    ls.add_argument("target", help="Layer index or name")

    ls = layer_sub.add_parser("set")
    ls.add_argument("target", help="Layer index or name")
    ls.add_argument("--name")
    ls.add_argument("--visible")
    ls.add_argument("--opacity", type=int)
    ls.add_argument("--locked")

    ls = layer_sub.add_parser("move")
    ls.add_argument("target")
    ls.add_argument("position", type=int)

    ls = layer_sub.add_parser("duplicate")
    ls.add_argument("target")

    ls = layer_sub.add_parser("merge-down")
    ls.add_argument("target")

    layer_sub.add_parser("flatten")

    # frame
    s = sub.add_parser("frame", help="Frame operations")
    s.add_argument("file")
    frame_sub = s.add_subparsers(dest="action")

    fs = frame_sub.add_parser("add")
    fs.add_argument("--copy-from", type=int)
    fs.add_argument("--position", type=int)

    fs = frame_sub.add_parser("remove")
    fs.add_argument("index", type=int)

    frame_sub.add_parser("list")

    fs = frame_sub.add_parser("select")
    fs.add_argument("index", type=int)

    fs = frame_sub.add_parser("set")
    fs.add_argument("index", type=int)
    fs.add_argument("--duration", type=int)

    fs = frame_sub.add_parser("duplicate")
    fs.add_argument("index", type=int)

    # tag
    s = sub.add_parser("tag", help="Tag operations")
    s.add_argument("file")
    tag_sub = s.add_subparsers(dest="action")

    ts = tag_sub.add_parser("add")
    ts.add_argument("name")
    ts.add_argument("from_frame", type=int)
    ts.add_argument("to_frame", type=int)
    ts.add_argument("--direction", choices=["forward", "reverse", "pingpong"])

    ts = tag_sub.add_parser("remove")
    ts.add_argument("name")

    tag_sub.add_parser("list")

    # transform
    s = sub.add_parser("transform", help="Transform operations")
    s.add_argument("file")
    s.add_argument("--layer", "-l", type=int)
    s.add_argument("--frame", "-f", type=int)
    t_sub = s.add_subparsers(dest="action")

    t_sub.add_parser("flip-h", help="Flip horizontally")
    t_sub.add_parser("flip-v", help="Flip vertically")

    ts = t_sub.add_parser("rotate")
    ts.add_argument("degrees", type=int, choices=[90, 180, 270])

    ts = t_sub.add_parser("resize")
    ts.add_argument("new_width", type=int)
    ts.add_argument("new_height", type=int)

    ts = t_sub.add_parser("crop")
    ts.add_argument("x", type=int)
    ts.add_argument("y", type=int)
    ts.add_argument("w", type=int)
    ts.add_argument("h", type=int)

    t_sub.add_parser("trim")

    # palette
    s = sub.add_parser("palette", help="Palette operations")
    s.add_argument("file")
    p_sub = s.add_subparsers(dest="action")
    p_sub.add_parser("show")
    ps = p_sub.add_parser("set")
    ps.add_argument("name")
    p_sub.add_parser("list")
    ps = p_sub.add_parser("add")
    ps.add_argument("color")

    # export
    s = sub.add_parser("export", help="Export sprite")
    s.add_argument("file", help=".tpa file")
    s.add_argument("output", help="Output file (png)")
    s.add_argument("--frame", "-f", type=int)
    s.add_argument("--scale", "-s", type=int, default=1)
    s.add_argument("--spritesheet", action="store_true")
    s.add_argument("--columns", type=int)
    s.add_argument("--json", action="store_true", help="Export JSON metadata")

    # import
    s = sub.add_parser("import", help="Import image")
    s.add_argument("input", help="Input image file")
    s.add_argument("output", help="Output .tpa file")

    # batch
    s = sub.add_parser("batch", help="Batch commands from JSON")
    s.add_argument("file", help=".tpa file")
    s.add_argument("--input", "-i", default="-", help="JSON file (- for stdin)")

    # edit (TUI)
    s = sub.add_parser("edit", help="Interactive TUI editor")
    s.add_argument("file", help=".tpa file")
    s.add_argument("--width", type=int)
    s.add_argument("--height", type=int)

    return p


COMMANDS = {
    "new": cmd_new, "view": cmd_view, "info": cmd_info,
    "pixel": cmd_pixel, "line": cmd_line, "rect": cmd_rect,
    "ellipse": cmd_ellipse, "circle": cmd_circle, "fill": cmd_fill,
    "erase": cmd_erase, "layer": cmd_layer, "frame": cmd_frame,
    "tag": cmd_tag, "transform": cmd_transform, "palette": cmd_palette_cmd,
    "export": cmd_export, "import": cmd_import, "batch": cmd_batch,
    "edit": cmd_edit,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    handler = COMMANDS.get(args.command)
    if handler:
        try:
            handler(args)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
