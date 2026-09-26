#!/usr/bin/python3
# =============================================================================
#  imagetest.mu — NomadNet page: display images converted by ~/img2mu.py
#  Place in: ~/.nomadnetwork/storage/pages/imagetest.mu
#
#  Drops every *.mu block found in ~/.nomadnetwork/images/ onto one page, so
#  converting a new picture is: run img2mu.py with --out into that directory,
#  reload the page. Nothing here needs editing.
#
#  Images live OUTSIDE storage/pages/ on purpose. Anything inside pages/ is
#  servable as a page in its own right, and a bare colour block served that way
#  would be a confusing half-page with no heading or navigation.
#
#  The .mu blocks are raw micron: U+2580 half-block characters carrying a
#  foreground colour (top pixel) and background colour (bottom pixel), so one
#  character is two stacked pixels. They are printed verbatim -- no escaping,
#  or the colour codes would render as literal text.
# =============================================================================

import os
import glob
import datetime

IMAGE_DIR = os.path.expanduser("~/.nomadnetwork/images")

# c=0 re-executes on every visit, so a newly converted image appears on reload
# rather than being served from cache.
print("#!c=0")
print("`l`Ffd0Image converter test`f")
print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("`F888Micron has no image support. These are drawn with U+2580 half-block")
print("characters: each cell's foreground colour is the top pixel and its")
print("background colour the bottom pixel, so one character carries two")
print("stacked pixels. Converted with img2mu.py.`f")
print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# Which viewer you are reading this in changes what you see. A real terminal
# has a true fixed character grid, and MeshChatX pins its cell width in CSS,
# so both draw a straight right edge. MeshChat and rBrowser let each cell take
# the font's fractional glyph advance inside a per-line div, so columns round
# differently on every row and the edge frays.
print("`F888Straight right edge in: `f`F0f0NomadNet browser, MeshChatX, reticulum.site`f")
print("`F888Frayed edge in: `f`Ffa0MeshChat, rBrowser`f`F888 - a renderer layout bug,")
print("not the image. Same file, different result.`f")
print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

blocks = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.mu")))

if not blocks:
    print()
    print("`Ff00No converted images found in " + IMAGE_DIR + "`f")
    print("`F888Create one with:`f")
    print("`F0fd  ~/img2mu.py picture.png --width 60 --out " + IMAGE_DIR + "/picture.mu`f")

for path in blocks:
    name = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            block = f.read().rstrip("\n")
    except Exception as e:
        print("`Ff00Could not read " + name + ": " + str(e) + "`f")
        continue

    lines = block.split("\n")
    rows = len(lines)
    # Character width = number of half-block glyphs on the widest line. The
    # colour codes are not printable width, so they must not be counted.
    cols = max((l.count("▀") for l in lines), default=0)
    nbytes = len(block.encode("utf-8"))

    # Is there a source image beside it to compare against?
    stem = os.path.splitext(path)[0]
    source = ""
    for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        if os.path.isfile(stem + ext):
            source = os.path.basename(stem + ext)
            break

    print()
    print("`Ffd0" + name + "`f")
    print("`F888  " + str(cols) + " x " + str(rows) + " characters  =  "
          + str(cols) + " x " + str(rows * 2) + " pixels`f")
    print("`F888  " + ("%.1f kB" % (nbytes / 1024.0) if nbytes >= 1024
                       else "%d B" % nbytes) + " of micron`f")
    if source:
        print("`F888  source: " + source + "`f")
    print()
    print(block)
    print("`b`f")
    print("`F0f2━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

print()
print("`F0fd`[cell aspect calibration`:/page/calibrate.mu`]`f")
print("`F888  use it if circles come out as ovals in your viewer`f")
print()
print("`F888Generated " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      + " · source images and .mu blocks both in " + IMAGE_DIR + "`f")
print("`a")
