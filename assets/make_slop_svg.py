"""Draw the slop leaderboard as an animated bar chart.

    python3 assets/make_slop_svg.py assets/leaderboard-2026-08-06.ndjson assets/slop.svg

The input is the raw output of the vibecheck leaderboard run (one JSON object
per repo, `density` = findings per 1,000 lines). Regenerate the chart from that
file rather than editing the SVG, so the picture can never drift from the
measurement behind it.

Notes on the constraints, because they are not obvious:

  - Bars are <rect> elements animating their width. An earlier version drew them
    as block characters revealed by a sliding clip mask, positioned with a
    hardcoded character width. That width is a guess that is wrong on any
    machine whose monospace font differs, and consecutive block glyphs leave
    hairline gaps, so the clip edge stepped across every character boundary
    instead of gliding. Geometry has no font metrics in it and glides anywhere.
  - Only system monospace for the labels. GitHub serves an SVG in a README as an
    image, and browsers refuse to fetch external resources in that context, so a
    webfont would silently fall back.
  - The animation runs once and freezes. Looping is what makes animated READMEs
    unbearable on a page you visit repeatedly.
  - Light and dark both live in the file. GitHub cannot theme an image from
    outside it.
"""
import json
import sys

LINE_H = 19
PAD_X = 18
PAD_Y = 16
LABEL_W = 108     # px reserved for the repo name column
GAP = 8
BAR_W = 236       # px, full-scale bar
BAR_H = 11
VALUE_W = 46      # px reserved for the number on the right
DRAW = 0.95       # seconds for one bar to reach full width
STAGGER = 0.075   # seconds between one row starting and the next
EASE = "0.16 1 0.3 1"


def short(slug):
    """openai/codex -> codex. The org adds nothing at this width."""
    return slug.split("/")[-1]


def main(src, out):
    rows = [json.loads(line) for line in open(src) if line.strip()]
    # Cleanest first: the finding is the distance between the ends, so leading
    # with the worst repo would read as a pile-on rather than a measurement.
    rows.sort(key=lambda r: r["density"])
    peak = max(r["density"] for r in rows)

    width = PAD_X * 2 + LABEL_W + GAP + BAR_W + VALUE_W
    row_y = lambda i: PAD_Y + 34 + i * LINE_H
    height = row_y(len(rows) - 1) + LINE_H + 14
    bar_x = PAD_X + LABEL_W + GAP

    parts = []
    for i, r in enumerate(rows):
        name, density = short(r["slug"]), r["density"]
        w = density / peak * BAR_W
        y, delay, top = row_y(i), i * STAGGER, row_y(i) - 11
        parts.append(
            f'  <text class="nm" x="{PAD_X}" y="{y}" style="animation-delay:{delay:.2f}s">{name}</text>\n'
            f'  <rect class="tk" x="{bar_x}" y="{top}" width="{BAR_W}" height="{BAR_H}" rx="1.5"/>\n'
            f'  <rect class="br" x="{bar_x}" y="{top}" width="0" height="{BAR_H}" rx="1.5">'
            f'<animate attributeName="width" from="0" to="{w:.1f}" dur="{DRAW}s" '
            f'begin="{delay:.2f}s" fill="freeze" calcMode="spline" keySplines="{EASE}"/></rect>\n'
            f'  <text class="vl" x="{width - PAD_X}" y="{y}" text-anchor="end" '
            f'style="animation-delay:{delay + DRAW * 0.6:.2f}s">{density:.1f}</text>'
        )

    alt = (f"AI slop findings per 1,000 lines across {len(rows)} AI coding tools: "
           f"{short(rows[0]['slug'])} cleanest at {rows[0]['density']:.1f}, "
           f"{short(rows[-1]['slug'])} noisiest at {rows[-1]['density']:.1f}")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{alt}">
<style>
  svg{{background:#0d1117}}
  text{{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}}
  .ttl{{fill:#e6edf3;font-size:12.5px}}
  .nm{{fill:#9198a1}} .vl{{fill:#e6edf3}} .tk{{fill:#21262d}} .br{{fill:#3fb950}}
  .nm,.vl,.ttl{{opacity:0;animation:fi .3s ease-out forwards}}
  @keyframes fi{{to{{opacity:1}}}}
  @media (prefers-color-scheme:light){{
    svg{{background:#ffffff}} .ttl,.vl{{fill:#1f2328}} .nm{{fill:#59636e}}
    .tk{{fill:#eaeef2}} .br{{fill:#1a7f37}}
  }}
  @media (prefers-reduced-motion:reduce){{
    .nm,.vl,.ttl{{animation:none;opacity:1}}
  }}
</style>
<text class="ttl" x="{PAD_X}" y="{PAD_Y + 14}">ai slop findings per 1,000 lines &#183; {len(rows)} ai coding tools</text>
{chr(10).join(parts)}
</svg>
"""
    open(out, "w").write(svg)
    print(f"{out}: {len(rows)} rows, {width}x{height}, {len(svg)} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
