#!/usr/bin/python3
# =============================================================================
#  calibrate.mu — find this viewer's character-cell aspect ratio
#  Place in: ~/.nomadnetwork/storage/pages/calibrate.mu
#
#  WHY THIS PAGE EXISTS
#  --------------------
#  Micron images are drawn with U+2580 half-blocks: one character cell carries
#  two vertically stacked pixels. Whether those pixels come out SQUARE depends
#  entirely on the shape of the renderer's character cell, and that differs
#  between viewers -- NomadNet's terminal UI, MeshChat's browser renderer and
#  rBrowser all use different fonts and line heights.
#
#  Guessing from font metrics does not settle it: a browser's "line-height:
#  normal" is not simply ascent+descent, and Nerd Fonts carry unusually large
#  vertical metrics because of their icon glyphs. Measuring by eye against a
#  known shape is both simpler and more trustworthy.
#
#  Each block below is the SAME circle, inscribed in a square, converted with a
#  different --cell-aspect. Exactly one will look right in YOUR viewer.
# =============================================================================

import os
import glob
import re

CALIB_DIR = os.path.expanduser("~/.nomadnetwork/images/calib")

print("#!c=0")
print("`l`Ffd0Cell aspect calibration`f")
print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("`F888Each block is the SAME image: a white circle inscribed in a green")
print("square, with a red crosshair. Only the --cell-aspect differs.")
print()
print("Find the one where the`f `FfffCIRCLE TOUCHES ALL FOUR SIDES`f `F888of the")
print("green square and looks round.")
print()
print("  too WIDE  -> circle overflows top and bottom -> pick a HIGHER value")
print("  too TALL  -> circle pulls away from left and right -> pick a LOWER one")
print()
print("Then convert future images with that value:")
print("`F0fd  img2mu.py pic.png --width 60 --cell-aspect <value>`f")
print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

blocks = sorted(glob.glob(os.path.join(CALIB_DIR, "a*.mu")))

if not blocks:
    print()
    print("`Ff00No calibration blocks found in " + CALIB_DIR + "`f")

for path in blocks:
    name = os.path.basename(path)
    m = re.match(r"a([0-9.]+)\.mu$", name)
    aspect = m.group(1) if m else name

    try:
        with open(path, "r", encoding="utf-8") as f:
            block = f.read().rstrip("\n")
    except Exception as e:
        print("`Ff00Could not read " + name + ": " + str(e) + "`f")
        continue

    lines = block.split("\n")
    cols = max((l.count("▀") for l in lines), default=0)

    print()
    print("`Ffd0--cell-aspect " + aspect + "`f  `F888(" + str(cols) + " x "
          + str(len(lines)) + " chars)`f")
    print()
    print(block)
    print("`b`f")
    print("`F0f2────────────────────────────────────────")

print()
print("`F888The value is a property of the VIEWER, not the image. A block that")
print("looks right here may look stretched in a different client.`f")
print()
print("`F0fd`[back to image converter test`:/page/imagetest.mu`]`f")
print("`a")
