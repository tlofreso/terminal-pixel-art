# TPA (Terminal Pixel Art) - Claude Code Skill Guide

This project contains `tpa`, a terminal-first pixel art editor. You can create, edit, and export pixel art entirely from the CLI. All commands are run via `uv run tpa`.

## Quick Reference

```bash
# Create a sprite
uv run tpa new <file>.tpa <width> <height> [--bg <color>] [--palette pico8]

# View it
uv run tpa view <file>.tpa

# Export to PNG
uv run tpa export <file>.tpa <output>.png --scale 8
```

## Drawing Commands

All drawing commands take the file as the first arg, coordinates as ints, and color as hex (`"#ff0000"`) or name (`red`). Use `-q` to suppress output. Use `--layer N` / `--frame N` to target specific layers/frames.

```bash
uv run tpa pixel <file> <x> <y> <color>           # single pixel (omit color to read)
uv run tpa line <file> <x1> <y1> <x2> <y2> <color>
uv run tpa rect <file> <x1> <y1> <x2> <y2> <color> [--fill]
uv run tpa ellipse <file> <x1> <y1> <x2> <y2> <color> [--fill]
uv run tpa circle <file> <cx> <cy> <radius> <color> [--fill]
uv run tpa fill <file> <x> <y> <color>             # flood fill
uv run tpa erase <file> <x> <y>                    # single pixel
uv run tpa erase <file> --rect X0 Y0 X1 Y1         # region
uv run tpa erase <file> --all                       # clear cel
```

## Batch Mode (Preferred for Complex Art)

Pipe JSON to stdin for multi-operation drawings. This is the most efficient way to create pixel art — use it for anything beyond a few strokes.

```bash
cat <<'EOF' | uv run tpa batch <file>.tpa
{
  "commands": [
    {"op": "fill", "x": 0, "y": 0, "color": "#1d2b53"},
    {"op": "rect", "x1": 2, "y1": 2, "x2": 13, "y2": 13, "color": "#ff004d", "fill": true},
    {"op": "line", "x1": 0, "y1": 0, "x2": 15, "y2": 15, "color": "white"},
    {"op": "ellipse", "x1": 3, "y1": 3, "x2": 12, "y2": 12, "color": "#ffec27", "fill": false},
    {"op": "pixel", "x": 8, "y": 8, "color": "#00e436"},
    {"op": "layer_add", "name": "Overlay"},
    {"op": "layer_select", "index": 1},
    {"op": "frame_add"},
    {"op": "frame_select", "index": 1}
  ]
}
EOF
```

**Batch ops:** `pixel` (x, y, color), `line` (x1, y1, x2, y2, color), `rect` (x1, y1, x2, y2, color, fill), `ellipse` (x1, y1, x2, y2, color, fill), `fill` (x, y, color), `layer_add` (name), `layer_select` (index), `frame_add` (copy_from?), `frame_select` (index).

## Layers, Frames, Tags

```bash
uv run tpa layer <file> list
uv run tpa layer <file> add <name>
uv run tpa layer <file> select <index-or-name>
uv run tpa layer <file> set <target> --opacity 128 --visible false
uv run tpa layer <file> remove|duplicate|merge-down|flatten <target>

uv run tpa frame <file> list
uv run tpa frame <file> add [--copy-from N]
uv run tpa frame <file> select <index>
uv run tpa frame <file> set <index> --duration 200

uv run tpa tag <file> add <name> <from> <to> [--direction forward|reverse|pingpong]
```

## Transforms

```bash
uv run tpa transform <file> flip-h
uv run tpa transform <file> flip-v
uv run tpa transform <file> rotate <90|180|270>
uv run tpa transform <file> resize <w> <h>       # nearest-neighbor
uv run tpa transform <file> crop <x> <y> <w> <h>
uv run tpa transform <file> trim                  # auto-remove empty borders
```

## Palettes

Built-in presets: `pico8`, `db16`, `db32`, `grayscale`, `basic`.

```bash
uv run tpa palette <file> set pico8
uv run tpa palette <file> show
```

## Import / Export

```bash
uv run tpa export <file>.tpa out.png --scale 8              # single frame
uv run tpa export <file>.tpa sheet.png --spritesheet --json  # all frames
uv run tpa import input.png output.tpa                       # PNG -> editable .tpa
```

## Pixel Art Technique Tips

- **Plan your palette first.** Use `--palette pico8` or `db16` for cohesive color.
- **Work back to front:** fill background, then large shapes, then details. Later batch ops overwrite earlier ones.
- **Use `--fill` for solid shapes**, omit it for outlines.
- **Flood fill (`fill`) is great for backgrounds** — fill the canvas first, then draw on top.
- **Subtract to create shapes:** draw a filled shape, then overdraw part of it with the background color (e.g., draw a full moon, then carve a crescent by overlaying a shifted circle in the background color).
- **Batch mode is essential** for anything with more than ~5 operations. It's atomic (one save) and much faster.
- **Always export with `--scale 8`** (or higher) so the PNG is viewable — raw 16x16 PNGs are tiny.
- **Colors:** hex `"#rrggbb"` or `"#rrggbbaa"`, or names: `black`, `white`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `gray`, `transparent`.

## File Format

`.tpa` files are human-readable JSON. Pixels are stored as hex strings (`"#ff004d"`) or `null` for transparent. You can read and hand-edit them if needed.

## Examples

See `examples/` for reference sprites with both `.tpa` source and `.png` exports: crescent moon
