"""Draw the slop leaderboard as an animated bar chart.

    python3 assets/make_slop_svg.py assets/leaderboard-2026-08-06.ndjson assets/slop.svg

The input is the raw output of the vibecheck leaderboard run (one JSON object
per repo, `density` = findings per 1,000 lines). Regenerate the chart from that
file rather than editing the SVG, so the picture can never drift from the
measurement behind it.

Notes on the constraints, because none of them are obvious:

  - Bars are <rect> elements whose width is animated. An early version drew them
    as block characters revealed by a sliding clip mask, positioned with a
    hardcoded character width. That width is a guess, wrong on any machine whose
    monospace font differs, and consecutive block glyphs leave hairline gaps, so
    the mask stepped across every character boundary instead of gliding.
    Geometry carries no font metrics and moves the same everywhere.

  - The animation LOOPS, with most of the cycle spent still. A one-shot version
    shipped first and was effectively invisible: it fired the moment the image
    loaded, ran for two seconds and froze, which on a profile page happens
    during render, before a reader's eye arrives. An animation nobody witnesses
    is just complexity. Every README demo GIF loops for the same reason.

  - The animation is CSS, not SMIL. A media query cannot disable SMIL, so a SMIL
    version would keep moving for readers who asked their OS for less motion.
    CSS keyframes honour `prefers-reduced-motion`.

  - Only system monospace for the labels. GitHub serves an SVG in a README as an
    image, and browsers refuse to fetch external resources in that context, so a
    webfont would silently fall back.

  - Light and dark both live in the file. GitHub cannot theme an image from the
    outside.
"""
import json
import sys

LINE_H = 19
PAD_L = 0         # flush with the readme's text column; the image floats left
                  # of the copy, so any left padding reads as a misalignment
PAD_R = 26        # gutter between the chart and the text wrapping beside it
PAD_T = 0         # the title's baseline then lands level with the first line
                  # of the paragraph alongside it
LABEL_W = 108     # px reserved for the repo name column
GAP = 8
BAR_W = 236       # px, full-scale bar
BAR_H = 11
VALUE_W = 46      # px reserved for the number on the right

DRAW = 1.5        # seconds for a bar to reach full width
HOLD = 6.0        # seconds the finished chart sits still
RETRACT = 0.5     # seconds to collapse before the cycle repeats
STAGGER = 0.055   # seconds between one row starting and the next
CYCLE = DRAW + HOLD + RETRACT


def short(slug):
    """openai/codex -> codex. The org adds nothing at this width."""
    return slug.split("/")[-1]


def main(src, out):
    rows = [json.loads(line) for line in open(src) if line.strip()]
    # Cleanest first: the finding is the distance between the ends, so leading
    # with the worst repo would read as a pile-on rather than a measurement.
    rows.sort(key=lambda r: r["density"])
    peak = max(r["density"] for r in rows)

    width = PAD_L + LABEL_W + GAP + BAR_W + VALUE_W + PAD_R
    row_y = lambda i: PAD_T + 32 + i * LINE_H
    height = row_y(len(rows) - 1) + 6
    bar_x = PAD_L + LABEL_W + GAP

    # Keyframe stops, as percentages of one cycle.
    k_drawn = DRAW / CYCLE * 100
    k_held = (DRAW + HOLD) / CYCLE * 100

    parts = []
    for i, r in enumerate(rows):
        name, density = short(r["slug"]), r["density"]
        w = density / peak * BAR_W
        y, delay, top = row_y(i), i * STAGGER, row_y(i) - 11
        parts.append(
            f'  <text class="nm" x="{PAD_L}" y="{y}">{name}</text>\n'
            f'  <rect class="tk" x="{bar_x}" y="{top}" width="{BAR_W}" height="{BAR_H}" rx="1.5"/>\n'
            f'  <rect class="br" x="{bar_x}" y="{top}" width="0" height="{BAR_H}" rx="1.5" '
            f'style="--w:{w:.1f}px;animation-delay:{delay:.2f}s"/>\n'
            f'  <text class="vl" x="{width - PAD_R}" y="{y}" text-anchor="end">{density:.1f}</text>'
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
  .br{{animation:draw {CYCLE:g}s linear infinite}}
  @keyframes draw{{
    0%{{width:0}}
    {k_drawn:.2f}%{{width:var(--w);animation-timing-function:cubic-bezier(.16,1,.3,1)}}
    {k_held:.2f}%{{width:var(--w)}}
    100%{{width:0;animation-timing-function:cubic-bezier(.5,0,.6,1)}}
  }}
  @media (prefers-reduced-motion:reduce){{
    .br{{animation:none;width:var(--w)}}
  }}
  @media (prefers-color-scheme:light){{
    svg{{background:#ffffff}} .ttl,.vl{{fill:#1f2328}} .nm{{fill:#59636e}}
    .tk{{fill:#eaeef2}} .br{{fill:#1a7f37}}
  }}
</style>
<text class="ttl" x="{PAD_L}" y="{PAD_T + 14}">ai slop findings per 1,000 lines &#183; {len(rows)} ai coding tools</text>
{chr(10).join(parts)}
</svg>
"""
    open(out, "w").write(svg)
    print(f"{out}: {len(rows)} rows, {width}x{height}, {CYCLE:g}s cycle, {len(svg)} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
