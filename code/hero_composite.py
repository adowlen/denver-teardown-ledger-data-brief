"""Composite the headline figure over the generated hero illustration.
Adapted from the Nashville building permit applications package
(2026-11-04): a TOP gradient scrim over the generated illustration's
clean dark field (hero_source/), with the narrative scene below.
All text is read from stats.json at composite time, so the hero can
never carry a figure the stats do not (sync gate, standards 10.3).
hero-headline.txt carries the same text for the record.

Usage: hero_composite.py [pct|spread] [output-path]
"""
import json
import pathlib
import sys
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).resolve().parent.parent
stats = json.loads((root / "stats.json").read_text())
cands = sorted((root / "hero_source").glob("*.webp")) + \
    sorted((root / "hero_source").glob("*.png")) if (root / "hero_source").exists() else []
if not cands:
    raise SystemExit("no hero illustration in hero_source/ - hero stays pending")
img = Image.open(cands[0]).convert("RGB")
W, H = img.size

# Top gradient scrim over the art's clean dark field: strongest at the
# top edge, fading out before the narrative scene begins.
band = int(H * 0.42)
overlay = Image.new("L", (1, band))
for yy in range(band):
    t = yy / band
    overlay.putpixel((0, yy), int(215 * (1 - t) ** 1.5))
overlay = overlay.resize((W, band))
scrim = Image.new("RGB", (W, band), (10, 13, 16))
img.paste(scrim, (0, 0), overlay)
d = ImageDraw.Draw(img)


def font(size, bold=True):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(p, size)


def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


cw = stats["citywide"]
variant = sys.argv[1] if len(sys.argv) > 1 else "pct"
srcline = ("Machine Readable - Denver assessor sales, permit and demolition registers, and HOST "
           "income-restricted inventory, January 2020 - October 2026 (warehouse snapshot 2026-11-01)")
if variant == "pct":
    headline = f"{stats['paired_share_in_zero_backstop_pct']:.1f}%"
    sub = (f"of Denver's {cw['paired_cycles']} completed teardown cycles closed in neighborhoods where the "
           f"HOST inventory records no income-restricted homes")
else:
    headline = f"${cw['paired_median_spread']:,.0f}"
    sub = (f"median gross spread between purchase price and first resale across Denver's {cw['paired_cycles']} "
           f"completed teardown cycles: a median buy of ${cw['paired_median_buy']:,.0f} replaced by a median "
           f"first sale of ${cw['paired_median_sell']:,.2f}")

MAXW = int(W * 0.88)
d.text((56, int(H * 0.05)), headline, font=font(int(H * 0.115)), fill=(245, 168, 0))
sub_f = font(int(H * 0.032), bold=False)
y = int(H * 0.05) + int(H * 0.145)
for line in wrap(sub, sub_f, MAXW):
    d.text((58, y), line, font=sub_f, fill=(242, 242, 242))
    y += int(H * 0.046)
src_f = font(int(H * 0.021), bold=False)
for line in wrap(srcline, src_f, MAXW):
    d.text((58, y + 8), line, font=src_f, fill=(150, 210, 200))
    y += int(H * 0.032)
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else (root / "hero.png")
img.save(out)
print("hero", variant, img.size, "from", cands[0].name, "->", out)
print("Headline:", headline)
print("Sub:", sub)
print("Source line:", srcline)
