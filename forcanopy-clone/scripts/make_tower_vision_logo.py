"""
Regenerates src/components/TowerVisionLogo.tsx as a "TOWER VISION" wordmark.

Letterforms come from the project's own Figtree variable font (the family the
site already loads), so these are real typeface outlines rather than invented
geometry. Vertical metrics are matched to the previous wordmark:

  cap height  33.600 px
  baseline    34.176 px
  stem/cap    0.1657  -> Figtree wght 640
  viewBox     0 0 <ink-width> 35

Outlines are converted with a TransformPen, so single-argument commands
(H/V) are handled correctly instead of being hand-parsed.

Each letter is emitted as its own <g class="logo-letter"> so the existing
per-letter bounce animation keeps working untouched; only the number of groups
and the delay step change (the cascade still spans the same 0.55s window).
"""
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = __file__.rsplit("/", 2)[0]
FONT = ROOT + "/public/fonts/f7aa21714c1c53f8-s.p.e3544bb0.woff2"
OUT = ROOT + "/src/components/TowerVisionLogo.tsx"
TEXT = "TOWER VISION"

WEIGHT = 640
CAP = 33.6
BASELINE = 34.176
TRACKING = 1.36      # px, matched to the old C->A advance
CASCADE = 0.55       # total stagger window, same as the old wordmark
VIEWBOX_H = 35

COMPONENT = """export function TowerVisionLogo() {{
  return (
    <svg
      width="{w}"
      height="35"
      viewBox="0 0 {w} 35"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="overflow-visible h-[22px] w-auto text-onbackground"
      role="img"
      aria-label="Tower Vision"
    >
{body}
    </svg>
  );
}}
"""


def fmt_delay(x):
    s = ("%.3f" % x).rstrip("0").rstrip(".")
    return s or "0"


def glyph_bbox(gs, name):
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return bp.bounds


def build(weight=WEIGHT, tracking=TRACKING, text=TEXT):
    f = TTFont(FONT)
    instantiateVariableFont(f, {"wght": weight}, inplace=True, updateFontNames=False)
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"].metrics

    # real cap height from the 'H' outline, not its advance width
    hx0, hy0, hx1, hy1 = glyph_bbox(gs, cmap[ord("H")])
    scale = CAP / (hy1 - hy0)

    # lay the word out in font units first
    pen_x, placed, right = 0.0, [], 0.0
    for ch in text:
        if ch == " ":
            pen_x += hmtx[cmap[ord(" ")]][0] + tracking / scale
            continue
        name = cmap[ord(ch)]
        x0, _, x1, _ = glyph_bbox(gs, name)
        placed.append((ch, name, pen_x, x0 * scale))
        right = max(right, (pen_x + x1) * scale)          # both in px
        pen_x += hmtx[name][0] + tracking / scale

    # one shared shift so the whole word starts at x = 0
    shift = placed[0][3]
    vb_w = round(right - shift + 1.0)
    step = CASCADE / max(len(placed) - 1, 1)

    letters = []
    for i, (ch, name, pen, _lsb) in enumerate(placed):
        out = SVGPathPen(gs)
        # font units (y up) -> svg (y down), scaled to CAP, advanced by `pen`,
        # then shifted so the word's left ink edge sits at x = 0
        gs[name].draw(TransformPen(
            out, (scale, 0, 0, -scale, pen * scale - shift, BASELINE)))
        letters.append((ch, out.getCommands(), i * step))
    return letters, vb_w


def emit(letters, vb_w, dest=OUT):
    rows = []
    for _, d, delay in letters:
        rows.append(
            '      <g className="logo-letter"'
            ' style={{ animationDelay: "' + fmt_delay(delay) + 's" }}>\n'
            '        <path d="' + d + '" fill="currentColor" />\n'
            "      </g>"
        )
    open(dest, "w").write(COMPONENT.format(w=vb_w, body="\n".join(rows)) + "\n")
    return vb_w


if __name__ == "__main__":
    letters, vb_w = build()
    step = CASCADE / max(len(letters) - 1, 1)
    print("letters=%d  viewBox=0 0 %d 35  weight=%d  tracking=%.2f  step=%.3fs"
          % (len(letters), vb_w, WEIGHT, TRACKING, step))
    emit(letters, vb_w)

    # flat (unanimated) variants for the footer, matching the pair that was
    # already there: same wordmark, one ink colour per theme
    for name, ink in (("tower-vision-logo-light.svg", "#101D46"),
                      ("tower-vision-logo-dark.svg", "#F8FAFF")):
        body = "".join('<path d="%s" fill="%s"/>' % (d, ink) for _, d, _ in letters)
        open(ROOT + "/public/" + name, "w").write(
            '<svg width="%d" height="35" viewBox="0 0 %d 35" fill="none" '
            'xmlns="http://www.w3.org/2000/svg">%s</svg>\n' % (vb_w, vb_w, body))
        print("wrote public/" + name)

    bare = "".join(
        '<g class="logo-letter"><path d="%s" fill="#101d46"/></g>' % d
        for _, d, _ in letters)
    open("/tmp/logo_bare.svg", "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="35" '
        'viewBox="0 0 %d 35" fill="none">%s</svg>' % (vb_w, vb_w, bare))
    print("wrote src/components/TowerVisionLogo.tsx + /tmp/logo_bare.svg")
