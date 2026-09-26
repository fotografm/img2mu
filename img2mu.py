#!/usr/bin/python3
"""img2mu — turn an image into a NomadNet micron (.mu) colour block.

HOW THE PICTURE IS MADE
-----------------------
Micron has no image support. Pictures are drawn with the half-block trick:
every character cell is U+2580 UPPER HALF BLOCK (▀), whose FOREGROUND colour
paints the top half of the cell and whose BACKGROUND colour paints the bottom
half. One character therefore carries TWO vertically stacked pixels, so a grid
of W x R characters displays W x 2R pixels.

    `B<bottom>`F<top>▀      one cell = two pixels

Because a terminal cell is about twice as tall as it is wide, two pixels
stacked in one cell come out very close to square. The converter relies on
that when working out the height.

THE COLOUR TRAP
---------------
Micron colours are exactly THREE hex digits after `F (foreground) or `B
(background) -- NomadNet's parser reads line[i+1:i+4] and no more. That looks
like 4096 colours, but it is not. Urwid maps those digits onto the xterm-256
colour cube, and the mapping is lossy:

    digits 0,1,2 -> 0x00      7,8,9 -> 0x87      c,d -> 0xd7
    digits 3,4,5,6 -> 0x5f    a,b   -> 0xaf      e,f -> 0xff

Six levels per channel, so only 216 colours are actually reachable. Quantising
to that cube up front is what keeps the rendered image faithful; feeding
arbitrary hex in and hoping is how you get colour shifts you cannot explain.

USAGE
    ./img2mu.py photo.png --width 100 > page.mu
    ./img2mu.py photo.png --width 100 --dither --preview check.png
"""

import argparse
import sys

from PIL import Image

BLOCK = "▀"

# The six channel levels micron can actually produce, and the digit to emit
# for each. Any digit in a group works; these are simply canonical.
LEVELS = (0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff)
DIGITS = ("0", "3", "7", "a", "c", "f")


def build_palette():
    """The 216 colours micron can really display, plus their micron codes."""
    colours, codes = [], []
    for ri, r in enumerate(LEVELS):
        for gi, g in enumerate(LEVELS):
            for bi, b in enumerate(LEVELS):
                colours.append((r, g, b))
                codes.append(DIGITS[ri] + DIGITS[gi] + DIGITS[bi])
    return colours, codes


COLOURS, CODES = build_palette()


def quantise(img, dither):
    """Snap every pixel to the 216-colour micron cube.

    Pillow needs the palette as a flat RGB list padded to 256 entries.
    """
    pal = Image.new("P", (1, 1))
    flat = [c for rgb in COLOURS for c in rgb]
    flat += [0, 0, 0] * (256 - len(COLOURS))
    pal.putpalette(flat)
    d = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    return img.convert("RGB").quantize(palette=pal, dither=d)


def convert(path, width, dither, cell_aspect=0.5):
    src = Image.open(path)

    # Flatten transparency onto black, or RGBA edges become noise.
    if src.mode in ("RGBA", "LA", "P"):
        src = src.convert("RGBA")
        bg = Image.new("RGBA", src.size, (0, 0, 0, 255))
        src = Image.alpha_composite(bg, src)
    src = src.convert("RGB")

    # How tall to make the pixel grid.
    #
    # cell_aspect is the renderer's character cell width / height. A cell holds
    # two stacked pixels, so on screen each pixel is cell_w wide by cell_h/2
    # tall -- a pixel aspect of 2 * cell_aspect. At cell_aspect 0.5 pixels are
    # square and the grid simply keeps the source ratio. Anything else has to
    # be compensated for, or circles come out as ovals:
    #
    #     px_h = px_w * (h/w) * 2 * cell_aspect
    #
    # Rows must be even so the bottom half of the last cell is real image
    # rather than padding.
    w, h = src.size
    px_h = max(2, round(width * (h / w) * 2 * cell_aspect))
    if px_h % 2:
        px_h += 1

    img = src.resize((width, px_h), Image.LANCZOS)
    q = quantise(img, dither)
    idx = q.load()

    lines = []
    for row in range(px_h // 2):
        out = []
        cur_fg = cur_bg = None
        for x in range(width):
            top = idx[x, row * 2]          # foreground
            bot = idx[x, row * 2 + 1]      # background
            # Emit a colour code only when it CHANGES. A run of identical
            # cells would otherwise roughly double the page size.
            #
            # Emitting one on every cell was tested (2026-09-24) on the theory
            # that differing span counts per row caused the frayed right edge
            # some viewers show. It did not help -- both encodings frayed
            # identically, while the SAME file renders with a straight edge on
            # reticulum.site. The cause is renderer-side, not the encoding:
            # MeshChat and rBrowser wrap each micron line in its own <div>, so
            # fractional glyph advances round independently per line, whereas
            # reticulum.site keeps the whole page in one <pre> text flow.
            if bot != cur_bg:
                out.append("`B" + CODES[bot])
                cur_bg = bot
            if top != cur_fg:
                out.append("`F" + CODES[top])
                cur_fg = top
            out.append(BLOCK)
        out.append("`b`f")                 # reset, so the next line is clean
        lines.append("".join(out))

    return lines, width, px_h, q


def preview(q, width, px_h, path, cell_aspect=0.5, scale=4):
    """Render what the viewer will actually show.

    The preview must be stretched by the pixel aspect (2 * cell_aspect),
    otherwise it shows square pixels and quietly hides the very distortion
    --cell-aspect exists to correct.
    """
    rgb = q.convert("RGB")
    pw = int(round(width * scale * 2 * cell_aspect))
    ph = px_h * scale
    rgb.resize((pw, ph), Image.NEAREST).save(path)


def main():
    ap = argparse.ArgumentParser(description="Convert an image to a micron colour block.")
    ap.add_argument("image")
    ap.add_argument("--width", type=int, default=80,
                    help="width in CHARACTERS (default 80). Also the pixel width.")
    ap.add_argument("--dither", action="store_true",
                    help="Floyd-Steinberg. Good for photos, bad for pixel art and flat logos.")
    ap.add_argument("--cell-aspect", type=float, default=0.5, metavar="A",
                    help="renderer's character cell width/height (default 0.5, "
                         "which makes pixels square in a terminal). Raise it if "
                         "circles come out wide, lower it if they come out tall. "
                         "Run the calibration page to find your viewer's value.")
    ap.add_argument("--preview", metavar="PNG",
                    help="write a PNG of exactly what NomadNet will render")
    ap.add_argument("--out", metavar="MU", help="write to a file instead of stdout")
    args = ap.parse_args()

    lines, width, px_h, q = convert(args.image, args.width, args.dither,
                                   args.cell_aspect)

    if args.preview:
        preview(q, width, px_h, args.preview, args.cell_aspect)
        print("preview written: %s" % args.preview, file=sys.stderr)

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print("wrote %s" % args.out, file=sys.stderr)
    else:
        sys.stdout.write(text)

    # Report real bytes, not characters: U+2580 is 3 bytes in UTF-8, so a
    # character count understates a page's size on the wire by roughly 3x --
    # which matters over LoRa.
    nbytes = len(text.encode("utf-8"))
    print("%d x %d characters  =  %d x %d pixels  (%s on the wire)"
          % (width, px_h // 2, width, px_h,
             "%.1f kB" % (nbytes / 1024) if nbytes >= 1024 else "%d B" % nbytes),
          file=sys.stderr)
    if width > 78:
        print("note: %d columns is wider than an 80-column terminal; "
              "narrow windows will wrap it." % width, file=sys.stderr)


if __name__ == "__main__":
    main()
