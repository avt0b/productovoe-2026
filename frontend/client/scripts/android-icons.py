"""Иконка APK из resources/icon.png — значок на прозрачном фоне.

    uv run --no-project --with pillow python scripts/android-icons.py

Пишет в android/app/src/main/res:
- mipmap-*/ic_launcher_foreground.png — передний слой адаптивной иконки
  (Android 8+). Слой 108 dp, лаунчер показывает середину 72 dp и режет её своей
  маской (круг, скруглённый квадрат). Значок чуть крупнее середины: маска
  срезает внешнюю рамку, а надпись и птица остаются целиком;
- mipmap-*/ic_launcher.png и ic_launcher_round.png — для старых лаунчеров;
- values/ic_launcher_background.xml — задний слой, цвет рамки значка.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "resources" / "icon.png"
RES = ROOT / "android" / "app" / "src" / "main" / "res"

# Плотность экрана -> множитель к dp.
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
LEGACY_DP = 48
ADAPTIVE_DP = 108
# Сколько dp из 108 занимает значок на переднем слое: видно 72, остальное — под маской.
BADGE_DP = 75
# Цвет рамки значка — им заполнено то, что маска покажет вокруг значка.
BACKGROUND = "#6E643F"


def badge() -> Image.Image:
    """Значок, обрезанный по непрозрачной части и выровненный в квадрат."""
    image = Image.open(SOURCE).convert("RGBA")
    box = image.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
    image = image.crop(box)
    side = max(image.size)
    square = Image.new("RGBA", (side, side))
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return square


def centered(image: Image.Image, canvas: int, size: int) -> Image.Image:
    out = Image.new("RGBA", (canvas, canvas))
    scaled = image.resize((size, size), Image.LANCZOS)
    offset = (canvas - size) // 2
    out.paste(scaled, (offset, offset), scaled)
    return out


def round_mask(image: Image.Image) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, image.width - 1, image.height - 1), fill=255)
    out = Image.new("RGBA", image.size)
    out.paste(image, (0, 0), Image.composite(image.getchannel("A"), mask, mask))
    return out


def main() -> None:
    source = badge()
    for density, scale in DENSITIES.items():
        folder = RES / f"mipmap-{density}"
        legacy = round(LEGACY_DP * scale)
        # У старых иконок поле по краю, как у системных: 1 dp с каждой стороны.
        inner = round((LEGACY_DP - 2) * scale)
        centered(source, legacy, inner).save(folder / "ic_launcher.png", optimize=True)
        # Круглая — тот же значок в круге: заполняем круг им целиком, рамка по углам уходит.
        round_mask(centered(source, legacy, round(legacy * 1.05))).save(folder / "ic_launcher_round.png", optimize=True)
        adaptive = round(ADAPTIVE_DP * scale)
        centered(source, adaptive, round(BADGE_DP * scale)).save(folder / "ic_launcher_foreground.png", optimize=True)
    (RES / "values" / "ic_launcher_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <color name="ic_launcher_background">{BACKGROUND}</color>\n</resources>\n',
        encoding="utf-8",
    )
    print("готово:", ", ".join(DENSITIES))


if __name__ == "__main__":
    main()
