"""Draw the slop leaderboard as an animated monospace bar chart.

    python3 assets/make_slop_svg.py assets/leaderboard-2026-08-06.ndjson assets/slop.svg

The input is the raw output of the vibecheck leaderboard run (one JSON object
per repo, `density` = findings per 1,000 lines). Regenerate the chart from that
file rather than editing the SVG, so the picture can never drift from the
measurement behind it.

Notes on the constraints, because they are not obvious:

  - Only system monospace fonts. GitHub serves an SVG in a README as an image,
    and browsers refuse to fetch external resources in that context, so a
    webfont would silently fall back and knock every bar out of alignment.
  - Bar geometry is in character widths, not pixels, so the blocks line up with
    the labels at whatever size the glyphs actually render.
  - The animation runs once and freezes. Looping is what makes animated READMEs
    unbearable on a page you visit repeatedly.
  - Light and dark both live in the file. GitHub cannot theme an image from
    outside it.
"""
import json
import sys

CHAR_W = 8.4      # advance width of the 13px monospace glyph, measured
LINE_H = 19
PAD_X = 18
PAD_Y = 16
NAME_COLS = 12    # label column, in characters
BAR_COLS = 28     # bar column, in characters
STAGGER = 0.055   # seconds between one row starting and the next
DRAW = 0.5        # seconds for a single bar to reach full width


def short(slug):
    """openai/codex -> codex. The org adds nothing at this width."""
    return slug.split("/")[-1]


def main(src, out):
    rows = [json.loads(line) for line in open(src) if line.strip()]
    # Cleanest first: the finding is the distance between the ends, so leading
    # with the worst repo would read as a pile-on rather than a measurement.
    rows.sort(key=lambda r: r["density"])
    peak = max(r["density"] for r in rows)

    width = int(PAD_X * 2 + (NAME_COLS + 1 + BAR_COLS + 6) * CHAR_W)
    row_y = lambda i: PAD_Y + 34 + i * LINE_H
    height = int(row_y(len(rows) - 1) + LINE_H + 14)
    bar_x = PAD_X + NAME_COLS * CHAR_W + CHAR_W * 0.6

    parts = []
    for i, r in enumerate(rows):
        name, density = short(r["slug"]), r["density"]
        filled = round(density / peak * BAR_COLS)
        y, delay = row_y(i), i * STAGGER
        parts.append(
            f'  <text class="nm" x="{PAD_X}" y="{y}" style="animation-delay:{delay:.2f}s">{name}</text>\n'
            f'  <text class="tk" x="{bar_x:.1f}" y="{y}" style="animation-delay:{delay:.2f}s">{"·" * BAR_COLS}</text>\n'
            f'  <g clip-path="url(#c{i})"><text class="br" x="{bar_x:.1f}" y="{y}">{"█" * filled}</text></g>\n'
            f'  <clipPath id="c{i}"><rect x="{bar_x:.1f}" y="{y - LINE_H + 4}" height="{LINE_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{filled * CHAR_W:.1f}" dur="{DRAW}s" '
            f'begin="{delay:.2f}s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></rect></clipPath>\n'
            f'  <text class="vl" x="{width - PAD_X}" y="{y}" text-anchor="end" '
            f'style="animation-delay:{delay + 0.35:.2f}s">{density:.1f}</text>'
        )

    alt = (f"AI slop findings per 1,000 lines across {len(rows)} AI coding tools: "
           f"{short(rows[0]['slug'])} cleanest at {rows[0]['density']:.1f}, "
           f"{short(rows[-1]['slug'])} noisiest at {rows[-1]['density']:.1f}")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{alt}">
<style>
  svg{{background:#0d1117}}
  text{{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}}
  .ttl{{fill:#e6edf3;font-size:12.5px;letter-spacing:.02em}}
  .nm{{fill:#9198a1}} .tk{{fill:#21262d}} .br{{fill:#3fb950}} .vl{{fill:#e6edf3}}
  .nm,.tk,.vl,.ttl{{opacity:0;animation:fi .35s ease-out forwards}}
  @keyframes fi{{to{{opacity:1}}}}
  @media (prefers-color-scheme:light){{
    svg{{background:#ffffff}} .ttl,.vl{{fill:#1f2328}} .nm{{fill:#59636e}}
    .tk{{fill:#eaeef2}} .br{{fill:#1a7f37}}
  }}
  @media (prefers-reduced-motion:reduce){{
    .nm,.tk,.vl,.ttl{{animation:none;opacity:1}}
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
