"""Core data model: Sprite, Layer, Cel, Color."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import copy


@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int = 255

    def to_hex(self) -> str:
        if self.a == 255:
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"

    @classmethod
    def from_hex(cls, s: str) -> Color:
        s = s.lstrip("#")
        if len(s) == 6:
            return cls(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        if len(s) == 8:
            return cls(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16))
        if len(s) == 3:
            return cls(int(s[0]*2, 16), int(s[1]*2, 16), int(s[2]*2, 16))
        raise ValueError(f"Invalid hex color: {s}")

    @classmethod
    def from_name(cls, name: str) -> Color:
        names = {
            "black": cls(0, 0, 0), "white": cls(255, 255, 255),
            "red": cls(255, 0, 0), "green": cls(0, 255, 0), "blue": cls(0, 0, 255),
            "yellow": cls(255, 255, 0), "cyan": cls(0, 255, 255), "magenta": cls(255, 0, 255),
            "orange": cls(255, 165, 0), "purple": cls(128, 0, 128),
            "gray": cls(128, 128, 128), "grey": cls(128, 128, 128),
            "transparent": cls(0, 0, 0, 0),
        }
        if name.lower() in names:
            return names[name.lower()]
        raise ValueError(f"Unknown color name: {name}")

    def blend_over(self, other: Color) -> Color:
        if self.a == 255:
            return Color(self.r, self.g, self.b, 255)
        if self.a == 0:
            return other
        sa = self.a / 255.0
        da = other.a / 255.0
        oa = sa + da * (1 - sa)
        if oa == 0:
            return Color(0, 0, 0, 0)
        r = (self.r * sa + other.r * da * (1 - sa)) / oa
        g = (self.g * sa + other.g * da * (1 - sa)) / oa
        b = (self.b * sa + other.b * da * (1 - sa)) / oa
        return Color(int(r), int(g), int(b), int(oa * 255))

    def with_alpha(self, a: int) -> Color:
        return Color(self.r, self.g, self.b, a)

    def __eq__(self, other):
        if not isinstance(other, Color):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a

    def __hash__(self):
        return hash((self.r, self.g, self.b, self.a))


def parse_color(s: str) -> Color:
    """Parse a color from hex string or named color."""
    if s.startswith("#"):
        return Color.from_hex(s)
    try:
        return Color.from_name(s)
    except ValueError:
        return Color.from_hex(s)


@dataclass
class Cel:
    """Content of a specific layer at a specific frame."""
    width: int
    height: int
    pixels: list  # [y][x] -> Optional[Color]
    x_offset: int = 0
    y_offset: int = 0

    @classmethod
    def empty(cls, w: int, h: int) -> Cel:
        return cls(w, h, [[None] * w for _ in range(h)])

    def get_pixel(self, x: int, y: int) -> Optional[Color]:
        lx, ly = x - self.x_offset, y - self.y_offset
        if 0 <= lx < self.width and 0 <= ly < self.height:
            return self.pixels[ly][lx]
        return None

    def set_pixel(self, x: int, y: int, color: Optional[Color]):
        lx, ly = x - self.x_offset, y - self.y_offset
        if 0 <= lx < self.width and 0 <= ly < self.height:
            self.pixels[ly][lx] = color

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[y][x] = None

    def clone(self) -> Cel:
        pixels = [[c if c is None else Color(c.r, c.g, c.b, c.a) for c in row] for row in self.pixels]
        return Cel(self.width, self.height, pixels, self.x_offset, self.y_offset)


@dataclass
class Layer:
    name: str
    visible: bool = True
    opacity: int = 255
    blend_mode: str = "normal"
    locked: bool = False
    cels: dict = field(default_factory=dict)  # frame_index -> Cel

    def get_cel(self, frame: int) -> Optional[Cel]:
        return self.cels.get(frame)

    def ensure_cel(self, frame: int, w: int, h: int) -> Cel:
        if frame not in self.cels:
            self.cels[frame] = Cel.empty(w, h)
        return self.cels[frame]


@dataclass
class Tag:
    name: str
    from_frame: int
    to_frame: int
    color: str = "#6699cc"
    direction: str = "forward"  # forward, reverse, pingpong


@dataclass
class Sprite:
    width: int
    height: int
    layers: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    frame_count: int = 1
    frame_durations: list = field(default_factory=lambda: [100])
    palette: list = field(default_factory=list)
    active_layer: int = 0
    active_frame: int = 0
    name: str = ""

    @classmethod
    def new(cls, width: int, height: int, bg_color: Optional[Color] = None, name: str = "") -> Sprite:
        sprite = cls(width=width, height=height, name=name)
        layer = Layer(name="Background")
        cel = Cel.empty(width, height)
        if bg_color:
            for y in range(height):
                for x in range(width):
                    cel.pixels[y][x] = Color(bg_color.r, bg_color.g, bg_color.b, bg_color.a)
        layer.cels[0] = cel
        sprite.layers.append(layer)
        return sprite

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def flatten_pixel(self, x: int, y: int, frame: Optional[int] = None) -> Optional[Color]:
        """Get composited pixel from all visible layers."""
        if frame is None:
            frame = self.active_frame
        result = None
        for layer in self.layers:
            if not layer.visible:
                continue
            cel = layer.get_cel(frame)
            if cel is None:
                continue
            pixel = cel.get_pixel(x, y)
            if pixel is None:
                continue
            if layer.opacity < 255:
                pixel = pixel.with_alpha(int(pixel.a * layer.opacity / 255))
            if result is None:
                result = pixel
            else:
                result = pixel.blend_over(result)
        return result

    def current_layer(self) -> Layer:
        return self.layers[self.active_layer]

    def current_cel(self) -> Cel:
        return self.current_layer().ensure_cel(self.active_frame, self.width, self.height)

    def add_layer(self, name: str, position: Optional[int] = None) -> int:
        layer = Layer(name=name)
        for i in range(self.frame_count):
            layer.cels[i] = Cel.empty(self.width, self.height)
        if position is None:
            self.layers.append(layer)
            return len(self.layers) - 1
        self.layers.insert(position, layer)
        return position

    def remove_layer(self, index: int):
        if len(self.layers) <= 1:
            raise ValueError("Cannot remove last layer")
        self.layers.pop(index)
        if self.active_layer >= len(self.layers):
            self.active_layer = len(self.layers) - 1

    def add_frame(self, copy_from: Optional[int] = None, position: Optional[int] = None) -> int:
        if position is None:
            position = self.frame_count
        for layer in self.layers:
            # Shift existing cels at >= position
            new_cels = {}
            for fi, cel in layer.cels.items():
                new_cels[fi + 1 if fi >= position else fi] = cel
            if copy_from is not None and copy_from in layer.cels:
                new_cels[position] = layer.cels[copy_from].clone()
            else:
                new_cels[position] = Cel.empty(self.width, self.height)
            layer.cels = new_cels
        self.frame_count += 1
        self.frame_durations.insert(position, 100)
        return position

    def remove_frame(self, index: int):
        if self.frame_count <= 1:
            raise ValueError("Cannot remove last frame")
        for layer in self.layers:
            new_cels = {}
            for fi, cel in layer.cels.items():
                if fi == index:
                    continue
                new_cels[fi - 1 if fi > index else fi] = cel
            layer.cels = new_cels
        self.frame_count -= 1
        self.frame_durations.pop(index)
        if self.active_frame >= self.frame_count:
            self.active_frame = self.frame_count - 1

    def snapshot(self) -> Sprite:
        """Deep copy for undo."""
        return copy.deepcopy(self)
