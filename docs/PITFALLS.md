# Pitfalls

Everything here was measured, not reasoned about. Several of these look like converter bugs
and are not; two of them were first "solved" with a wrong answer derived from font metrics.
Each entry leads with the symptom, because that is what you will have when you meet it.

---

## Colour

### There are 216 colours, not 4096

**Symptom:** colours in the rendered page are close to the source but not right, and shift in
ways that make no sense.

Micron colour codes are exactly **three hex digits** after `` `F `` or `` `B `` — NomadNet's
parser reads `line[i+1:i+4]` and no more. Three hex digits looks like 4096 colours. It is
not: urwid maps those digits onto the **xterm-256 colour cube**, and the mapping is lossy.

Measured against urwid:

```
digits 0,1,2 -> 0x00      3,4,5,6 -> 0x5f      7,8,9 -> 0x87
       a,b   -> 0xaf      c,d     -> 0xd7      e,f   -> 0xff
```

Six levels per channel — **6³ = 216 reachable colours**. Feeding in arbitrary hex and hoping
is how you get colour shifts you cannot explain.

`img2mu.py` quantises to exactly that cube up front, so what Pillow picks is what the viewer
shows.

### Transparency becomes noise

Flatten RGBA onto a background before converting, or semi-transparent edges quantise to
speckle. The converter composites onto black.

---

## Geometry

### Do not derive cell aspect from font metrics

**Symptom:** circles render as ovals, and the number you calculated to fix it makes things
worse.

One character cell carries two stacked pixels, so whether those pixels are square depends
entirely on the renderer's cell shape — which differs per viewer. The compensation is:

```
px_h = px_w * (h/w) * 2 * cell_aspect
```

Both attempts to *calculate* `cell_aspect` were wrong:

- **From font tables.** Roboto Mono Nerd Font reports an advance of 0.600 em but
  ascent+descent of 1.319 em, because its icon glyphs inflate the vertical metrics. That
  predicted images about 9% too narrow, while the viewer was actually rendering them ~17%
  too wide.
- **From counting pixels off a screenshot.** Also wrong, and confidently so.

A browser's `line-height: normal` is **not** ascent + descent. Measure instead: render
`pages/calibrate.mu`, which shows the same circle at six aspect values, and pick the one
touching all four sides of its square.

### Keep `--cell-aspect` at 0.5

Measured on the calibration page: **0.50 is correct** for MeshChat (stock), rBrowser with
ASCII mode off, **and** reticulum.site. Only rBrowser's optional ASCII-mode toggle — which
sets `line-height: 1.0` — wants 0.60.

Earlier notes suggesting ~0.586 for MeshChat were wrong twice over; see above.

### Why viewers differ at all

- **MeshChat** forces `pre { font-family: Roboto Mono Nerd Font; line-height: normal }`,
  giving roughly a 0.6 × 1.02 em cell.
- **reticulum.site** sets no font at all, so the browser's default monospace gives about
  0.6 × 1.2 em — which is exactly the 1:2 cell that half-block art assumes.

That difference is the whole reason `--cell-aspect` exists.

### Rows must be even

Two pixels per cell means an odd pixel height leaves the bottom half of the last row as
padding rather than image. The converter rounds up.

---

## Rendering artefacts that are not your fault

### Frayed right edge, wavy vertical lines

**Symptom:** the right-hand edge of the image is ragged and vertical lines waver, in one
viewer but not another.

**This is a renderer bug, not the `.mu` file**, and which viewers show it has changed:

| viewer | right edge |
|---|---|
| reticulum.site | straight |
| **MeshChatX 4.9.1** | **straight** |
| MeshChat | frayed |
| rBrowser | frayed |

The cause is how the page is put into the DOM. reticulum.site emits the whole page as **one
`<pre>`**, newline-separated, with no per-line elements. MeshChat's `MicronParser.js` does
`markup.split("\n")` and creates a `<div>` per line. Independent block boxes plus a
fractional glyph advance — 0.6 em is 9.6 px at 16 px — means columns round differently on
each line.

**MeshChatX solves it without giving up per-line elements.** It wraps each monospace cell in
a span carrying an explicit width:

```css
.Mu-mnt { display: inline-block; width: 0.6em; text-align: center; white-space: pre; }
```

Once the cell width is stated rather than inherited from the font's fractional advance, every
row rounds identically and the edge is straight. Worth knowing if you maintain a Micron
renderer: the fix is one CSS rule, not a restructure.

**Tested and rejected:** emitting a colour code on every cell (a `--uniform-cells` option) on
the theory that differing span counts per row caused it. Both encodings frayed *identically*.
The option was removed. Nothing the converter can do; report it upstream.

### Hairline banding between rows in MeshChat

Each Micron line is a `<div>` of inline `<span>`s, and inline backgrounds fill the font
**content box**, not the line box. With `line-height: normal` that leaves a hairline gap
between rows.

Patching `line-height: 1` into MeshChat's `public/assets/*.css` fixes it without a rebuild
(useful, since Node is purged from that install) — but it tightens *all* text on every page,
so it was not applied.

---

## Size and quality

### Size is UTF-8 **bytes**, not characters

`▀` is three bytes. A 119 × 30 character block is about **20 kB** on the wire, not 3.5 kB.
That matters a great deal over LoRa. `img2mu.py` reports real byte counts for this reason.

Emitting a colour code only when it changes — rather than on every cell — is roughly a **3×
saving**, and is why the converter does it.

### Over 78 columns wraps

A standard 80-column terminal will wrap anything wider, and a wrapped half-block image is
destroyed rather than merely untidy. The converter warns above 78.

### `--dither` is usually wrong, even for photos

**Symptom:** the dithered version looks noisier *and* is bigger.

Measured on a photo at 60 × 60 (2026-09-24):

| | size | look |
|---|---|---|
| undithered | 13.9 kB | clearly cleaner |
| dithered | 18.7 kB | noisy |

Two reasons. At these resolutions there are too few pixels for the eye to blend the dither
pattern, so you see the pattern rather than the tone. And dithering breaks up runs of
identical colour, defeating the run-length saving.

Always render both and look at `--preview`.

### Crop tight — subject density beats every converter setting

Same photo, same 60 × 60 budget:

- Whole frame (two birds plus foliage) → mush.
- One bird's head → eye, facial patch and beak all readable.

Viewers magnify a 60 × 60 block to roughly 880 px, about 15×, so every pixel has to earn its
place. **Crop to the single subject before touching `--width` or `--dither`.**

Low resolution suits logos and line art. Test cards and dense photographs fall apart.

---

## NomadNet integration

### Keep images outside `storage/pages/`

Anything inside the pages directory is servable as a page in its own right, and a bare colour
block served that way is a confusing half-page with no heading or navigation. Put converted
blocks somewhere like `~/.nomadnetwork/images/` and have a page read them —
`pages/imagetest.mu` does exactly that.

### Use `#!c=0` on a gallery page

Without it the page is cached, and a newly converted image will not appear until something
else invalidates it.

### Print blocks verbatim

The `.mu` blocks are raw Micron. Do not escape them on the way out or the colour codes render
as literal text.

---

## Reading a page back

If you are parsing a Micron page from a **web gateway** rather than producing one:

- Colours arrive as **6-hex**, not 3-hex, because urwid has already expanded them to
  xterm-256 values.
- A single picture may be split across several `<pre class="micron-pre">` blocks. Stitch them
  on a shared column origin before trying to rebuild the image.
