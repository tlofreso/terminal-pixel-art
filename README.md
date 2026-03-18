# TODO
 - ensure support for uvx
 - do testing with larger formats
 - write blog post, be sure to cover:
    - Pattern for library skills from tiangolo: https://tiangolo.com/ideas/library-agent-skills/
    - Motivation for the project being yoto player art: https://yoto.space/pixel-art
 - Maybe push to pypi
 - Add more examples

# TPA - Terminal Pixel Art

An [Aseprite](https://www.aseprite.org/)-inspired pixel art editor built for the terminal. Use it as a **CLI** for scriptable pixel art, or launch the interactive **TUI** to draw with your keyboard.

![Crescent Moon](examples/rocket.png)

## Install

Requires Python 3.9+. Clone the repo and sync with [uv](https://docs.astral.sh/uv/):

```bash
git clone <repo-url> && cd terminal-pixel-art
uv sync
```

Then run commands with `uv run tpa`.

## Quick Start

```bash
# Create a 16x16 sprite with a black background and the PICO-8 palette
uv run tpa new my_sprite.tpa 16 16 --bg black --palette pico8

# Draw on it
uv run tpa rect my_sprite.tpa 2 2 13 13 "#ff004d" --fill
uv run tpa circle my_sprite.tpa 7 7 4 "#ffec27" --fill
uv run tpa line my_sprite.tpa 0 0 15 15 white

# View it in the terminal
uv run tpa view my_sprite.tpa

# Export to PNG (8x upscaled)
uv run tpa export my_sprite.tpa output.png --scale 8
```

## CLI Reference

Every command follows the pattern `uv run tpa <command> <file> [args]`.

### Creating & Viewing

| Command | Description |
|---|---|
| `tpa new <file> <w> <h>` | Create a new sprite |
| `tpa view <file>` | Render sprite in the terminal |
| `tpa info <file>` | Print sprite metadata |
| `tpa edit <file>` | Open interactive TUI editor |

**`new` options:**

```
--bg COLOR        Background color (hex like "#1d2b53" or name like "black")
--name NAME       Sprite name
--palette PRESET  Load a built-in palette (db16, db32, pico8, grayscale, basic)
```

**`view` options:**

```
-f, --frame N     Show a specific frame (0-indexed)
-z, --zoom N      Zoom level (default: 1)
-g, --grid        Show an 8x8 grid overlay
--ascii           Render as ASCII art instead of color blocks
-i, --info        Also print sprite metadata
```

### Drawing

All drawing commands target the active layer and frame by default. Override with `--layer N` / `--frame N`. Add `-q` to suppress output.

| Command | Description |
|---|---|
| `tpa pixel <file> <x> <y> [color]` | Set a pixel, or read its color if no color given |
| `tpa line <file> <x1> <y1> <x2> <y2> <color>` | Draw a line (Bresenham's algorithm) |
| `tpa rect <file> <x1> <y1> <x2> <y2> <color>` | Draw a rectangle (`--fill` for solid) |
| `tpa ellipse <file> <x1> <y1> <x2> <y2> <color>` | Draw an ellipse (`--fill` for solid) |
| `tpa circle <file> <cx> <cy> <r> <color>` | Draw a circle (`--fill` for solid) |
| `tpa fill <file> <x> <y> <color>` | Flood fill from a point (`--tolerance N`) |
| `tpa erase <file> [x] [y]` | Erase a pixel, a `--rect X0 Y0 X1 Y1`, or `--all` |

**Colors** can be specified as:
- Hex: `"#ff0000"`, `"#ff0000aa"` (with alpha), `"#f00"` (shorthand)
- Names: `black`, `white`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `gray`, `transparent`

### Layers

```bash
tpa layer <file> list                          # List all layers
tpa layer <file> add <name> [--position N]     # Add a layer
tpa layer <file> remove <index-or-name>        # Remove a layer
tpa layer <file> select <index-or-name>        # Set active layer
tpa layer <file> set <target> [options]        # Modify layer properties
tpa layer <file> move <target> <position>      # Reorder a layer
tpa layer <file> duplicate <target>            # Copy a layer
tpa layer <file> merge-down <target>           # Merge into layer below
tpa layer <file> flatten                       # Flatten all layers into one
```

**`set` options:** `--name`, `--visible true|false`, `--opacity 0-255`, `--locked true|false`

Layer list output uses these indicators:
```
 *[0] V. Background (opacity=255)    # * = active, V = visible, L = locked
  [1] .L Overlay (opacity=128)       # . = hidden/unlocked
```

### Frames & Animation

```bash
tpa frame <file> list                          # List all frames
tpa frame <file> add [--copy-from N] [--position N]  # Add a frame
tpa frame <file> remove <index>                # Remove a frame
tpa frame <file> select <index>                # Set active frame
tpa frame <file> set <index> --duration <ms>   # Set frame timing
tpa frame <file> duplicate <index>             # Duplicate a frame
```

### Tags

Tags label ranges of frames (e.g., "idle", "walk", "attack") for organizing animations.

```bash
tpa tag <file> add <name> <from> <to> [--direction forward|reverse|pingpong]
tpa tag <file> remove <name>
tpa tag <file> list
```

### Transforms

All transforms apply to every layer/frame unless scoped with `--layer N` / `--frame N`.

```bash
tpa transform <file> flip-h                    # Flip horizontally
tpa transform <file> flip-v                    # Flip vertically
tpa transform <file> rotate <90|180|270>       # Rotate clockwise
tpa transform <file> resize <w> <h>            # Resize (nearest-neighbor)
tpa transform <file> crop <x> <y> <w> <h>      # Crop to region
tpa transform <file> trim                      # Remove empty borders
```

### Palette

```bash
tpa palette <file> list                        # List available presets
tpa palette <file> show                        # Display current palette
tpa palette <file> set <preset>                # Load a preset (db16, db32, pico8, grayscale, basic)
tpa palette <file> add <color>                 # Append a color
```

### Import & Export

```bash
# Export single frame to PNG
tpa export <file> output.png --scale 4

# Export a specific frame
tpa export <file> output.png --frame 2

# Export all frames as a spritesheet
tpa export <file> sheet.png --spritesheet --columns 4

# Export spritesheet with JSON metadata
tpa export <file> sheet.png --spritesheet --json

# Import a PNG into a .tpa file
tpa import input.png output.tpa
```

PNG export/import requires [Pillow](https://python-pillow.org/), which is included as a dependency.

### Batch Mode

Execute many drawing operations at once by piping JSON to stdin:

```bash
cat <<'EOF' | uv run tpa batch my_sprite.tpa
{
  "commands": [
    {"op": "fill", "x": 0, "y": 0, "color": "#1d2b53"},
    {"op": "rect", "x1": 2, "y1": 2, "x2": 13, "y2": 13, "color": "#ff004d", "fill": true},
    {"op": "line", "x1": 0, "y1": 0, "x2": 15, "y2": 15, "color": "white"},
    {"op": "pixel", "x": 8, "y": 8, "color": "#00e436"},
    {"op": "ellipse", "x1": 4, "y1": 4, "x2": 11, "y2": 11, "color": "yellow", "fill": false},
    {"op": "layer_add", "name": "Overlay"},
    {"op": "layer_select", "index": 1},
    {"op": "frame_add"},
    {"op": "frame_select", "index": 1}
  ]
}
EOF
```

Or read from a file: `uv run tpa batch my_sprite.tpa -i commands.json`

**Supported batch operations:**

| op | Fields |
|---|---|
| `pixel` | `x`, `y`, `color` |
| `line` | `x1`, `y1`, `x2`, `y2`, `color` |
| `rect` | `x1`, `y1`, `x2`, `y2`, `color`, `fill` (optional bool) |
| `ellipse` | `x1`, `y1`, `x2`, `y2`, `color`, `fill` (optional bool) |
| `fill` | `x`, `y`, `color` |
| `layer_add` | `name` |
| `layer_select` | `index` |
| `frame_add` | `copy_from` (optional int) |
| `frame_select` | `index` |

## Interactive TUI

Launch with `uv run tpa edit <file>`. If the file doesn't exist, a new 16x16 sprite is created.

### Keybindings

**Tools:**

| Key | Tool |
|---|---|
| `b` | Pencil |
| `l` | Line |
| `u` | Rectangle |
| `o` | Ellipse |
| `c` | Circle |
| `g` | Flood fill |
| `e` | Eraser |
| `i` | Eyedropper (pick color) |

**Drawing:**

| Key | Action |
|---|---|
| Arrow keys | Move cursor |
| `Space` | Apply tool / set shape start point |
| `Enter` | Confirm shape (line, rect, ellipse, circle) |
| `Escape` | Cancel current shape |
| `f` | Toggle filled/outline mode for shapes |

**Navigation & View:**

| Key | Action |
|---|---|
| `+` / `-` | Zoom in / out |
| `#` | Toggle grid |
| `[` / `]` | Previous / next layer |
| `,` / `.` | Previous / next frame |
| `1` / `2` | Previous / next palette color |

**Editing:**

| Key | Action |
|---|---|
| `Ctrl+Z` | Undo (50 levels) |
| `Ctrl+Y` | Redo |
| `x` | Swap foreground/background color |
| `v` | Toggle layer visibility |
| `n` | Add new frame (copy of current) |
| `N` | Add new layer |
| `H` | Flip horizontally |
| `V` | Flip vertically |

**File:**

| Key | Action |
|---|---|
| `Ctrl+S` | Save |
| `q` | Quit (prompts if unsaved) |

### TUI Workflow

For shape tools (line, rect, ellipse, circle):
1. Press the tool key (e.g., `l` for line)
2. Move cursor to the start point, press `Space`
3. Move cursor to the end point, press `Space` or `Enter`

## File Format

Sprites are stored as `.tpa` files — human-readable JSON. The format stores layers, frames, cels, palette, tags, and per-pixel color data as hex strings.

```json
{
  "version": 1,
  "width": 16,
  "height": 16,
  "frame_count": 1,
  "layers": [
    {
      "name": "Background",
      "visible": true,
      "opacity": 255,
      "cels": {
        "0": {
          "width": 16,
          "height": 16,
          "pixels": [
            ["#1d2b53", "#1d2b53", null, ...],
            ...
          ]
        }
      }
    }
  ],
  "tags": [],
  "palette": ["#000000", "#1d2b53", ...]
}
```

Pixels are `null` for transparent, or hex color strings like `"#ff004d"`. This makes `.tpa` files easy to inspect, diff, and edit by hand or script.

## Examples

The [`examples/`](examples/) directory contains sample sprites. To recreate the crescent moon:

```bash
uv run tpa new examples/crescent_moon.tpa 16 16 --palette pico8

cat <<'EOF' | uv run tpa batch examples/crescent_moon.tpa
{
  "commands": [
    {"op": "fill", "x": 0, "y": 0, "color": "#1d2b53"},
    {"op": "ellipse", "x1": 3, "y1": 1, "x2": 13, "y2": 14, "color": "#ffec27", "fill": true},
    {"op": "ellipse", "x1": 6, "y1": 0, "x2": 15, "y2": 13, "color": "#1d2b53", "fill": true},
    {"op": "pixel", "x": 2, "y": 3, "color": "#fff1e8"},
    {"op": "pixel", "x": 12, "y": 2, "color": "#fff1e8"},
    {"op": "pixel", "x": 14, "y": 7, "color": "#fff1e8"},
    {"op": "pixel", "x": 1, "y": 10, "color": "#fff1e8"},
    {"op": "pixel", "x": 10, "y": 12, "color": "#fff1e8"},
    {"op": "pixel", "x": 13, "y": 13, "color": "#fff1e8"},
    {"op": "pixel", "x": 0, "y": 6, "color": "#fff1e8"},
    {"op": "pixel", "x": 14, "y": 4, "color": "#fff1e8"}
  ]
}
EOF

uv run tpa export examples/crescent_moon.tpa examples/crescent_moon.png --scale 8
```

## Architecture

| Module | Purpose |
|---|---|
| `model.py` | Core data structures: Sprite, Layer, Cel, Color with RGBA alpha compositing |
| `drawing.py` | Drawing algorithms: Bresenham's line, midpoint ellipse, flood fill |
| `render.py` | Terminal rendering via Unicode half-blocks (`▀`) and 24-bit ANSI color |
| `fileio.py` | JSON `.tpa` format serialization, PNG import/export via Pillow |
| `transform.py` | Flip, rotate, nearest-neighbor resize, crop, trim |
| `selection.py` | Rectangular and magic wand selection with set operations |
| `palette.py` | Built-in palettes: PICO-8, DawnBringer 16/32, grayscale, basic |
| `cli.py` | CLI with 19 subcommands |
| `tui.py` | Interactive curses-based editor |

## Inspired By

[Aseprite](https://www.aseprite.org/) — the best pixel art tool out there. TPA brings its core workflow to the terminal for scripting and keyboard-driven editing.
