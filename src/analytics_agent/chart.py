from html import escape

def render_svg(report):
    groups = report["statistics"]["groups"]
    height = 110 + 62*len(groups)
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}">',
              '<rect width="100%" height="100%" fill="#f8fafc"/>',
              '<text x="24" y="32" font-family="sans-serif" font-size="20">Observed conversion rates by channel</text>',
              '<text x="24" y="55" font-family="sans-serif" font-size="12">Individual Wilson 95% intervals; observational, not causal.</text>']
    scale = max(0.1, max(g["wilson_95_ci"][1] for g in groups))*1.1
    for index, group in enumerate(groups):
        y = 85 + index*62
        lo, hi = group["wilson_95_ci"]
        x = lambda v: 240+v/scale*370
        pieces.extend([f'<text x="24" y="{y+5}" font-family="sans-serif" font-size="14">{escape(group["channel"])}</text>',
                       f'<line x1="{x(lo):.2f}" y1="{y}" x2="{x(hi):.2f}" y2="{y}" stroke="#165e46" stroke-width="3"/>',
                       f'<circle cx="{x(group["rate"]):.2f}" cy="{y}" r="5" fill="#165e46"/>',
                       f'<text x="650" y="{y+5}" font-family="sans-serif" font-size="13">{group["rate"]:.1%} (n={group["events"]})</text>'])
    pieces.append('</svg>')
    return ''.join(pieces)
