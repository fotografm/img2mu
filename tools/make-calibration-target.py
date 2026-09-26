#!/usr/bin/env python3
"""
Draw the calibration target: a circle inscribed in a square.

Used with pages/calibrate.mu to find a viewer's character-cell aspect ratio by
eye. Convert this image at several --cell-aspect values; in the correct one the
circle touches all four sides of the square. Anything else shows it as an oval.

    ./make-calibration-target.py calib-target.png

Deliberately a generator rather than a checked-in PNG, so the shape it produces
is auditable — the whole point is that you trust what you are measuring against.
"""
import sys
from PIL import Image, ImageDraw

SIZE = 400
OUT = sys.argv[1] if len(sys.argv) > 1 else "calib-target.png"

img = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
d = ImageDraw.Draw(img)

# White square border, inset slightly so the outline is not clipped.
m = 8
d.rectangle([m, m, SIZE - 1 - m, SIZE - 1 - m], outline=(255, 255, 255), width=6)

# Circle inscribed in that square. Round only if the cell aspect is right.
d.ellipse([m, m, SIZE - 1 - m, SIZE - 1 - m], outline=(255, 96, 0), width=6)

# Centre cross, to make any vertical/horizontal stretch easier to see.
c = SIZE // 2
d.line([c, m, c, SIZE - 1 - m], fill=(64, 64, 64), width=2)
d.line([m, c, SIZE - 1 - m, c], fill=(64, 64, 64), width=2)

img.save(OUT)
print("wrote %s (%dx%d)" % (OUT, SIZE, SIZE))
