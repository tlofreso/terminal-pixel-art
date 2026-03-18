"""Built-in color palettes."""
from __future__ import annotations
from .model import Color

# DB16 - DawnBringer's 16-color palette
DB16 = [
    Color(20, 12, 28),    Color(68, 36, 52),    Color(48, 52, 109),
    Color(78, 74, 78),    Color(133, 76, 48),   Color(52, 101, 36),
    Color(208, 70, 72),   Color(117, 113, 97),  Color(89, 125, 206),
    Color(210, 125, 44),  Color(133, 149, 161),  Color(109, 170, 44),
    Color(210, 170, 153), Color(109, 194, 202), Color(218, 212, 94),
    Color(222, 238, 214),
]

# DB32 - DawnBringer's 32-color palette
DB32 = [
    Color(0, 0, 0),       Color(34, 32, 52),    Color(69, 40, 60),
    Color(102, 57, 49),   Color(143, 86, 59),   Color(223, 113, 38),
    Color(217, 160, 102), Color(238, 195, 154), Color(251, 242, 54),
    Color(153, 229, 80),  Color(106, 190, 48),  Color(55, 148, 110),
    Color(75, 105, 47),   Color(82, 75, 36),    Color(50, 60, 57),
    Color(63, 63, 116),   Color(48, 96, 130),   Color(91, 110, 225),
    Color(99, 155, 255),  Color(95, 205, 228),  Color(203, 219, 252),
    Color(255, 255, 255), Color(155, 173, 183), Color(132, 126, 135),
    Color(105, 106, 106), Color(89, 86, 82),    Color(118, 66, 138),
    Color(172, 50, 50),   Color(217, 87, 99),   Color(215, 123, 186),
    Color(143, 151, 74),  Color(138, 111, 48),
]

# PICO-8 palette
PICO8 = [
    Color(0, 0, 0),       Color(29, 43, 83),    Color(126, 37, 83),
    Color(0, 135, 81),    Color(171, 82, 54),   Color(95, 87, 79),
    Color(194, 195, 199), Color(255, 241, 232), Color(255, 0, 77),
    Color(255, 163, 0),   Color(255, 236, 39),  Color(0, 228, 54),
    Color(41, 173, 255),  Color(131, 118, 156), Color(255, 119, 168),
    Color(255, 204, 170),
]

# Grayscale
GRAYSCALE = [Color(i, i, i) for i in range(0, 256, 17)]  # 16 shades

# Basic named palette
BASIC = [
    Color(0, 0, 0),       Color(255, 255, 255), Color(255, 0, 0),
    Color(0, 255, 0),     Color(0, 0, 255),     Color(255, 255, 0),
    Color(0, 255, 255),   Color(255, 0, 255),   Color(128, 0, 0),
    Color(0, 128, 0),     Color(0, 0, 128),     Color(128, 128, 0),
    Color(0, 128, 128),   Color(128, 0, 128),   Color(128, 128, 128),
    Color(192, 192, 192),
]

PALETTES = {
    "db16": DB16,
    "db32": DB32,
    "pico8": PICO8,
    "grayscale": GRAYSCALE,
    "basic": BASIC,
}


def get_palette(name: str) -> list:
    name = name.lower()
    if name not in PALETTES:
        raise ValueError(f"Unknown palette: {name}. Available: {', '.join(PALETTES)}")
    return [Color(c.r, c.g, c.b, c.a) for c in PALETTES[name]]
