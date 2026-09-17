"""
Генерирует картинку-маркер для точки маршрута.

ARCore узнаёт картинку по особым точкам — углам и резким перепадам яркости.
Однотонные заливки, повторяющиеся узоры и симметрия ему не подходят, а голый
QR-код распознаётся плохо: у него повторяющаяся сетка. Поэтому маркер — это
мозаика из неповторяющихся фигур в цветах кейса, а QR стоит в углу как
дополнительный источник углов и как ссылка на точку для тех, у кого нет AR.

Нужны Pillow и qrcode:

    python -m pip install pillow qrcode
    python tools/make_marker.py --point-id wp-2 --title "Рубеж связистов" --step "Точка 2 из 4" \
        --out ar/src/main/assets/markers/wp-2.png

Печатать в ширину 30 см (A4 горизонтально с полями) — эта ширина зашита
в MarkerSpec.physicalWidthMeters. Напечатали крупнее — поправьте и там.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Цвета из макета Stitch.
PRIMARY = (50, 69, 35)
PRIMARY_LIGHT = (95, 120, 72)
TERTIARY = (103, 49, 0)
TERTIARY_FIXED = (255, 220, 198)
TERTIARY_DIM = (255, 183, 134)
SURFACE = (251, 249, 241)
INK = (49, 49, 43)

PALETTE = [PRIMARY, PRIMARY_LIGHT, TERTIARY, TERTIARY_FIXED, TERTIARY_DIM, INK, SURFACE]

WIDTH, HEIGHT = 1600, 1100
MARGIN = 48
MOSAIC_WIDTH = 960


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
    return ImageFont.load_default()


def mosaic(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], rng: random.Random) -> None:
    """Неповторяющиеся многоугольники разного размера: много углов, нет симметрии."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=SURFACE)
    for _ in range(420):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        radius = rng.choice([14, 22, 34, 52, 80]) * rng.uniform(0.7, 1.3)
        sides = rng.choice([3, 3, 4, 5])
        start = rng.uniform(0, math.tau)
        points = [
            (
                min(max(cx + radius * rng.uniform(0.6, 1.2) * math.cos(start + k * math.tau / sides), x0), x1),
                min(max(cy + radius * rng.uniform(0.6, 1.2) * math.sin(start + k * math.tau / sides), y0), y1),
            )
            for k in range(sides)
        ]
        draw.polygon(points, fill=rng.choice(PALETTE), outline=INK, width=rng.choice([1, 2, 3]))
    # Несколько колец и лучей поверх — длинные контрастные границы сквозь мозаику.
    for _ in range(9):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(40, 150)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rng.choice([INK, TERTIARY, PRIMARY]), width=rng.choice([6, 10]))
    for _ in range(7):
        draw.line(
            (rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(x0, x1), rng.uniform(y0, y1)),
            fill=rng.choice([INK, SURFACE, TERTIARY_FIXED]),
            width=rng.choice([5, 9]),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--point-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--step", default="")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, help="по умолчанию — из point-id, чтобы маркер воспроизводился")
    args = parser.parse_args()

    # Сид из идентификатора: у каждой точки свой узор, и повторный запуск даёт тот же файл.
    rng = random.Random(args.seed if args.seed is not None else args.point_id)

    image = Image.new("RGB", (WIDTH, HEIGHT), PRIMARY)
    draw = ImageDraw.Draw(image)

    # Мозаика рисуется на отдельном холсте и вклеивается: кольца и лучи у края
    # иначе вылезают за рамку на тёмное поле.
    panel_size = (MOSAIC_WIDTH, HEIGHT - 2 * MARGIN)
    panel = Image.new("RGB", panel_size, SURFACE)
    mosaic(ImageDraw.Draw(panel), (0, 0, panel_size[0] - 1, panel_size[1] - 1), rng)
    image.paste(panel, (MARGIN, MARGIN))
    mosaic_box = (MARGIN, MARGIN, MARGIN + MOSAIC_WIDTH, HEIGHT - MARGIN)
    draw.rectangle(mosaic_box, outline=TERTIARY_FIXED, width=6)

    text_x = MARGIN * 2 + MOSAIC_WIDTH
    draw.text((text_x, MARGIN + 10), "ТРОПА ПАМЯТИ", font=font(40, bold=True), fill=TERTIARY_DIM)
    draw.text((text_x, MARGIN + 70), args.step.upper(), font=font(30), fill=TERTIARY_FIXED)

    title_font = font(58, bold=True)
    y = MARGIN + 130
    line = ""
    for word in args.title.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=title_font) > WIDTH - text_x - MARGIN and line:
            draw.text((text_x, y), line, font=title_font, fill=SURFACE)
            y += 70
            line = word
        else:
            line = candidate
    draw.text((text_x, y), line, font=title_font, fill=SURFACE)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(f"marshruty://point/{args.point_id}")
    qr.make(fit=True)
    qr_size = WIDTH - text_x - MARGIN
    qr_image = qr.make_image(fill_color=INK, back_color=SURFACE).convert("RGB").resize((qr_size, qr_size), Image.NEAREST)
    qr_top = HEIGHT - MARGIN - qr_size - 60
    image.paste(qr_image, (text_x, qr_top))
    draw.text((text_x, qr_top + qr_size + 14), "Наведите камеру на картинку", font=font(28), fill=TERTIARY_FIXED)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out, optimize=True)
    print(f"записано: {args.out} ({args.out.stat().st_size // 1024} КБ, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
