"""Обложка для объявления Авито: текст поверх фото.

    python3 фото/обложка.py 1 фото.jpg обложка-1.jpg   # объявление 1А
    python3 фото/обложка.py 2 фото.jpg обложка-2.jpg   # объявление 2А
    python3 фото/обложка.py 1 - макет-1.jpg            # без фото — макет на условном фоне

Размер 1600 × 1200 (4:3). Текст держится в центральной части кадра,
чтобы не обрезаться в квадратном превью на телефоне.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 1200
SAFE_LEFT, SAFE_RIGHT = 260, 1340  # квадратная обрезка оставляет x 200–1400, плюс поле 60
ACCENT = (242, 140, 40)
WHITE = (255, 255, 255)
FONTS = Path(__file__).parent / "шрифты"

COVERS = {
    "1": {
        "title": ["Лазерная резка", "и гибка металла"],
        "points": [
            "от 1 детали, по чертежу или эскизу",
            "сталь до 12 мм, алюминий, нержавейка",
            "гибка до 6 мм, длина до 3,7 м",
        ],
        "badge": "Свой завод в Санкт-Петербурге",
    },
    "2": {
        "title": ["Металлоконструкции", "на заказ"],
        "points": [
            "от мелких изделий до крупных каркасов",
            "от раскроя до сварки в одном цехе",
            "сварщики НАКС, цех 3 200 м²",
        ],
        "badge": "Свой завод в Санкт-Петербурге",
    },
}


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"Montserrat-{weight}.ttf"), size)


def cover_crop(img):
    """Заполнить 1600 × 1200 без полей, лишнее обрезать по центру."""
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))


def placeholder():
    """Условный фон для макета: тёмный металл и искры, как у реза."""
    rnd = random.Random(7)
    row = Image.new("RGB", (W, 1))
    row.putdata([(int(28 + 30 * x / W), int(33 + 32 * x / W), int(40 + 34 * x / W)) for x in range(W)])
    bg = row.resize((W, H))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = 1180, 520
    g.ellipse((cx - 260, cy - 260, cx + 260, cy + 260), fill=(255, 120, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    bg = Image.composite(glow, bg, glow.convert("L").point(lambda v: min(255, v)))
    d = ImageDraw.Draw(bg)
    for _ in range(140):
        a = rnd.uniform(0.6, 2.6)
        r1, r2 = rnd.uniform(10, 60), rnd.uniform(120, 520)
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a)
        x2, y2 = cx + r2 * math.cos(a), cy + r2 * math.sin(a)
        d.line((x1, y1, x2, y2), fill=(255, rnd.randint(170, 230), 120), width=rnd.choice((1, 2, 2, 3)))
    d.rectangle((0, 880, W, H), fill=(36, 40, 46))
    return bg.filter(ImageFilter.GaussianBlur(1.2))


def shade(img):
    """Затемнение слева, чтобы белый текст читался на любом фото."""
    row = Image.new("L", (W, 1))
    row.putdata([225 if x / W < 0.5 else max(0, int(225 * (1 - (x / W - 0.5) / 0.42))) for x in range(W)])
    mask = row.resize((W, H))
    dark = Image.new("RGB", (W, H), (12, 15, 20))
    return Image.composite(dark, img, mask)


def fit(draw, text, weight, size, max_w):
    while size > 20:
        f = font(weight, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(weight, size)


def render(key, photo, out):
    spec = COVERS[key]
    img = placeholder() if photo in (None, "-") else cover_crop(Image.open(photo).convert("RGB"))
    img = shade(img)
    d = ImageDraw.Draw(img)
    x, max_w = SAFE_LEFT, SAFE_RIGHT - SAFE_LEFT

    title_size = min(
        fit(d, line, 800, 104, max_w).size for line in spec["title"]
    )
    tf = font(800, title_size)
    pf = min((fit(d, p, 600, 46, max_w - 44) for p in spec["points"]), key=lambda f: f.size)
    bf = font(700, 38)

    line_h = int(title_size * 1.12)
    block_h = 14 + 34 + len(spec["title"]) * line_h + 40 + len(spec["points"]) * int(pf.size * 1.7) + 50 + 76
    y = (H - block_h) // 2

    d.rectangle((x, y, x + 120, y + 14), fill=ACCENT)
    y += 14 + 34
    for line in spec["title"]:
        d.text((x, y), line, font=tf, fill=WHITE)
        y += line_h
    y += 40
    for p in spec["points"]:
        sq = int(pf.size * 0.42)
        top = y + int(pf.size * 0.62) - sq // 2
        d.rectangle((x, top, x + sq, top + sq), fill=ACCENT)
        d.text((x + 44, y), p, font=pf, fill=(235, 238, 242))
        y += int(pf.size * 1.7)
    y += 50
    tw = d.textlength(spec["badge"], font=bf)
    d.rounded_rectangle((x, y, x + tw + 56, y + 76), radius=38, fill=ACCENT)
    d.text((x + 28, y + 38), spec["badge"], font=bf, fill=(20, 20, 20), anchor="lm")

    img.save(out, quality=92)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in COVERS:
        sys.exit(__doc__)
    print(render(sys.argv[1], sys.argv[2], sys.argv[3]))
