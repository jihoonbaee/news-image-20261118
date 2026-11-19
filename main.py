#!/usr/bin/env python3
"""news-image-20261118 -- one image summing up Wednesday 18 November 2026.

Draws a newspaper-style front page (1024x1024 PNG) with pure Python 3.13
standard library only: no network, no third-party packages, no fonts on
disk. Text is rendered with a small built-in 5x7 bitmap font, and the PNG
is encoded by hand (zlib + struct). Output is fully deterministic: the
same input data always produces byte-identical output.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes: $MAKEFUN_OUTPUT_DIR/entry.png

REFRESH: to update the picture after 18 November 2026 has ended, edit the
STORIES list (and ALSO_TODAY) below, re-run main.py, and check entry.png.
Nothing else needs to change.
"""

import binascii
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------------------
# The day's stories (full-day edition: reported across 18 Nov 2026).
# Sources are listed in BUILD-REPORT.md. Keep headlines short: they render
# at scale 4 across ~850 px, about 35 characters per line, max 2 lines.
# ---------------------------------------------------------------------------

STORIES = [
    {
        "kicker": "CHINA  |  SUMMIT",
        "headline": "XI, PUTIN MEET BEFORE TRUMP SUMMIT",
        "sub": "Trilateral talks with Trump set for Thursday in Shenzhen; no agenda "
               "published.",
        "color": (178, 34, 34),      # red
        "icon": "globe",
    },
    {
        "kicker": "THE GULF  |  CONFLICT",
        "headline": "IRAN HITS KUWAIT, BAHRAIN BASES",
        "sub": "Tehran targets Ali Al Salem air base after a US strike on Qeshm "
               "Island.",
        "color": (11, 94, 106),      # teal
        "icon": "burst",
    },
    {
        "kicker": "PHILIPPINES  |  DIPLOMACY",
        "headline": "TRUMP HAILS BIG PHILIPPINES DEAL",
        "sub": "Manila calls it an economic understanding; Quad leaders meet in "
               "Manila.",
        "color": (31, 78, 140),      # blue
        "icon": "quad",
    },
    {
        "kicker": "UNITED STATES  |  MIDTERMS",
        "headline": "DEMOCRATS TAKE SENATE 56-44",
        "sub": "Peltola beats Sullivan in Alaska, the last midterm race to be "
               "called.",
        "color": (84, 62, 122),      # purple
        "icon": "ballot",
    },
    {
        "kicker": "BUSINESS  |  TECH",
        "headline": "NVIDIA REVENUE DOUBLES TO $115.8BN",
        "sub": "First results since co-founder Jensen Huang resigned; the board "
               "says he will not return as chief executive.",
        "color": (46, 125, 32),      # green
        "icon": "chip",
    },
    {
        "kicker": "RUSSIA  |  DISASTER",
        "headline": "RUSSIAN PLANE CRASH KILLS 19",
        "sub": "A military plane crashes in Siberia; all 19 people aboard are "
               "killed.",
        "color": (70, 80, 100),      # slate
        "icon": "plane",
    },
]

ALSO_TODAY = (
    "ALSO:  UN: 372 civilians killed in Ukraine in October  |  UK sanctions "
    "8 firms  |  1,500 migrants reach Canary Islands  |  Voyager 1 passes "
    "light-day mark"
)

DATE_LINE = "WEDNESDAY, 18 NOVEMBER 2026"
TITLE_LINE = "THE WORLD IN ONE PICTURE"
SUB_LINE = "Six stories that defined the day - the full day's news"
FOOT_NOTE = "Every story above was reported on Wednesday 18 November 2026."

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# Uppercase, lowercase, digits and common punctuation. Text is rendered in
# mixed case; unknown characters fall back to '?'.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "#####", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".###.", "....#"),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "..##."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "#####", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..##.", ".#..."),
    ":": (".....", ".....", "..#..", ".....", ".....", "..#..", "....."),
    ";": (".....", ".....", "..#..", ".....", ".....", "..#..", ".#..."),
    "'": (".#...", ".#...", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".###.", "#...#", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
}

GLYPH_W, GLYPH_H = 5, 7


def text_width(text, scale):
    """Pixel width of text at the given scale (1 px gap between glyphs)."""
    if not text:
        return 0
    return len(text) * (GLYPH_W * scale + scale) - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width px."""
    char_w = GLYPH_W * scale + scale
    max_chars = max(1, max_width // char_w)
    lines, current = [], ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if len(trial) <= max_chars:
            current = trial
        else:
            if current:
                lines.append(current)
            # A single over-long word is hard-split.
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Canvas: an RGB image held as a bytearray, with rect / line / circle / text.
# ---------------------------------------------------------------------------

W, H = 1024, 1024
PAPER = (247, 243, 234)
INK = (24, 28, 38)
GREY = (84, 88, 96)
NAVY = (18, 30, 54)
GOLD = (201, 162, 39)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
ROW_ALT = (240, 236, 226)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for t in range(thick):
            rr = r - t
            for yy in range(cy - rr, cy + rr + 1):
                dx = int((rr * rr - (yy - cy) ** 2) ** 0.5)
                self._set(cx - dx, yy, color)
                self._set(cx + dx, yy, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(GLYPH_H):
                bits = glyph[row]
                for col in range(GLYPH_W):
                    if bits[col] == "#":
                        self.fill_rect(
                            cx + col * scale, y + row * scale,
                            scale, scale, color)
            cx += (GLYPH_W + 1) * scale
        return cx

    def draw_text_centered(self, x, y, w, text, scale, color):
        tw = text_width(text, scale)
        self.draw_text(x + max(0, (w - tw) // 2), y, text, scale, color)


# ---------------------------------------------------------------------------
# Pictograms drawn in white inside each story's colour square.
# ---------------------------------------------------------------------------

def draw_icon(cv, kind, x, y, size, color):
    """Draw the pictogram for a story inside the square (x, y, size)."""
    cv.fill_rect(x, y, size, size, color)
    c = WHITE
    cx, cy = x + size // 2, y + size // 2
    if kind == "drone":
        # Quadcopter: body + four arms with rotors.
        cv.fill_rect(cx - 12, cy - 8, 24, 16, c)
        cv.fill_rect(cx - 3, cy - 3, 6, 6, color)
        for ax, ay in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            ex, ey = cx + ax * 30, cy + ay * 22
            cv.line(cx, cy, ex, ey, c)
            cv.fill_circle(ex, ey, 7, c)
            cv.fill_circle(ex, ey, 3, color)
    elif kind == "number372":
        cv.draw_text_centered(x, cy - 26, size, "372", 5, c)
        cv.draw_text_centered(x, cy + 16, size, "KILLED", 2, c)
    elif kind == "number8":
        cv.draw_text_centered(x, cy - 32, size, "8", 7, c)
        cv.draw_text_centered(x, cy + 20, size, "FIRMS", 2, c)
    elif kind == "boat":
        # Hull, mast, sail, waves.
        cv.line(cx - 34, cy + 8, cx + 34, cy + 8, c)
        cv.line(cx - 28, cy + 26, cx + 28, cy + 26, c)
        cv.line(cx - 34, cy + 8, cx - 28, cy + 26, c)
        cv.line(cx + 34, cy + 8, cx + 28, cy + 26, c)
        cv.fill_rect(cx - 28, cy + 10, 56, 14, c)
        cv.vline(cx + 2, cy - 34, 44, c)
        for dx in range(0, 26, 2):
            cv.line(cx + 4, cy - 32 + dx, cx + 4 + (26 - dx), cy - 6, c)
        for wy in (cy + 34, cy + 42):
            for wx in range(x + 8, x + size - 8, 16):
                cv.line(wx, wy, wx + 8, wy - 4, c)
                cv.line(wx + 8, wy - 4, wx + 16, wy, c)
    elif kind == "chip":
        cv.fill_rect(cx - 26, cy - 26, 52, 52, c)
        cv.fill_rect(cx - 15, cy - 15, 30, 30, color)
        cv.draw_text_centered(x, cy - 8, size, "AI", 2, c)
        for i in range(-1, 2):
            off = i * 18
            cv.fill_rect(cx + off - 2, cy - 36, 4, 10, c)
            cv.fill_rect(cx + off - 2, cy + 26, 4, 10, c)
            cv.fill_rect(cx - 36, cy + off - 2, 10, 4, c)
            cv.fill_rect(cx + 26, cy + off - 2, 10, 4, c)
    elif kind == "scales":
        # Balance: post, beam, two pans.
        cv.fill_rect(cx - 2, cy - 34, 4, 62, c)
        cv.fill_rect(cx - 30, cy - 34, 60, 4, c)
        cv.fill_rect(cx - 12, cy + 28, 24, 4, c)
        for sx in (-30, 30):
            cv.line(cx + sx, cy - 30, cx + sx - 12, cy - 8, c)
            cv.line(cx + sx, cy - 30, cx + sx + 12, cy - 8, c)
            cv.line(cx + sx - 12, cy - 8, cx + sx + 12, cy - 8, c)
            cv.line(cx + sx - 12, cy - 8, cx + sx, cy + 4, c)
            cv.line(cx + sx + 12, cy - 8, cx + sx, cy + 4, c)
    elif kind == "globe":
        # Globe: ring with meridian, equator and latitude lines.
        cv.ring(cx, cy, 32, c, 3)
        cv.vline(cx, cy - 32, 64, c)
        cv.hline(cx - 32, cy, 64, c)
        cv.line(cx - 24, cy - 20, cx + 24, cy - 20, c)
        cv.line(cx - 24, cy + 20, cx + 24, cy + 20, c)
    elif kind == "burst":
        # Explosion: bright centre with rays in every direction.
        cv.fill_circle(cx, cy, 10, c)
        for dx, dy in ((0, -34), (24, -24), (34, 0), (24, 24),
                       (0, 34), (-24, 24), (-34, 0), (-24, -24)):
            cv.line(cx, cy, cx + dx, cy + dy, c)
        for dx, dy in ((12, -30), (30, -12), (30, 12), (12, 30),
                       (-12, 30), (-30, 12), (-30, -12), (-12, -30)):
            cv.line(cx, cy, cx + dx, cy + dy, c)
    elif kind == "quad":
        # Four squares, two by two: the Quad grouping.
        for sx in (-20, 6):
            for sy in (-20, 6):
                cv.fill_rect(cx + sx, cy + sy, 14, 14, c)
    elif kind == "ballot":
        # Ballot box with a slot and a check mark.
        cv.fill_rect(cx - 26, cy - 6, 52, 34, c)
        cv.fill_rect(cx - 30, cy - 14, 60, 8, c)
        cv.fill_rect(cx - 12, cy - 12, 24, 4, color)
        cv.line(cx - 16, cy + 8, cx - 4, cy + 20, color)
        cv.line(cx - 4, cy + 20, cx + 18, cy - 2, color)
    elif kind == "plane":
        # Airliner in side view, nose right, with motion lines.
        cv.fill_rect(cx - 34, cy - 4, 64, 8, c)
        cv.fill_circle(cx + 30, cy, 5, c)
        cv.fill_rect(cx - 36, cy - 24, 6, 20, c)
        cv.fill_rect(cx - 40, cy - 24, 14, 5, c)
        cv.line(cx - 2, cy + 4, cx - 18, cy + 28, c)
        cv.line(cx + 1, cy + 4, cx - 15, cy + 28, c)
        cv.line(cx - 2, cy + 4, cx - 12, cy + 28, c)
        for mx in (-38, -46):
            cv.hline(cx + mx, cy + 2, 6, c)


# ---------------------------------------------------------------------------
# Layout and PNG encoding.
# ---------------------------------------------------------------------------

HEADER_H = 150
FOOTER_H = 78
MARGIN = 24
GAP = 10


def build_png():
    cv = Canvas(W, H, PAPER)

    # ---- Header -----------------------------------------------------------
    cv.fill_rect(0, 0, W, HEADER_H, NAVY)
    cv.fill_rect(0, HEADER_H - 6, W, 6, RED)
    cv.draw_text_centered(0, 20, W, TITLE_LINE, 3, GOLD)
    cv.draw_text_centered(0, 56, W, DATE_LINE, 5, WHITE)
    cv.draw_text_centered(0, 108, W, SUB_LINE, 2, (198, 205, 218))

    # ---- Story rows -------------------------------------------------------
    rows_top = HEADER_H + GAP
    rows_h = H - HEADER_H - FOOTER_H - 2 * GAP
    row_h = rows_h // len(STORIES)
    text_x = MARGIN + 118
    text_w = W - MARGIN - text_x

    for i, story in enumerate(STORIES):
        y = rows_top + i * row_h
        rh = row_h - 6
        bg = CARD if i % 2 == 0 else ROW_ALT
        cv.fill_rect(MARGIN, y, W - 2 * MARGIN, rh, bg)
        # Colour tab on the left edge.
        cv.fill_rect(MARGIN, y, 6, rh, story["color"])
        # Icon square.
        draw_icon(cv, story["icon"], MARGIN + 14, y + (rh - 96) // 2, 96,
                  story["color"])

        tx = text_x
        ty = y + 14
        cv.draw_text(tx, ty, story["kicker"], 2, story["color"])
        ty += 22
        head_lines = wrap_text(story["headline"], text_w, 4)
        for line in head_lines[:2]:
            cv.draw_text(tx, ty, line, 4, INK)
            ty += 30
        if len(head_lines) == 1:
            ty += 4
        sub_lines = wrap_text(story["sub"], text_w, 2)
        for line in sub_lines[:2]:
            cv.draw_text(tx, ty, line, 2, GREY)
            ty += 17

    # ---- Footer -----------------------------------------------------------
    fy = H - FOOTER_H + 4
    cv.fill_rect(0, H - FOOTER_H, W, 2, RED)
    foot_lines = wrap_text(ALSO_TODAY, W - 2 * MARGIN, 2)
    for line in foot_lines[:2]:
        cv.draw_text(MARGIN, fy, line, 2, INK)
        fy += 17
    cv.draw_text(MARGIN, fy + 2, FOOT_NOTE, 2, GREY)

    return encode_png(cv)


def encode_png(cv):
    """Encode the canvas as a PNG (colour type 2, 8-bit, filter 0)."""
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw += cv.px[start:start + cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    data = build_png()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
