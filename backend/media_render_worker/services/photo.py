"""Исходное фото бойца -> ровный RGB JPEG.

Фото с телефона часто лежит «на боку» и развёрнуто только тегом EXIF — ffmpeg
и SadTalker этот тег не читают, и боец в ролике оказался бы лёжа. PNG с
прозрачностью и WebP приводим к тому же JPEG, чтобы дальше не гадать о формате."""

import io

from PIL import Image, ImageOps, UnidentifiedImageError


class PhotoUnreadable(Exception):
    """Файл — не картинка или повреждён."""


def normalize(content: bytes, *, max_side: int) -> bytes:
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise PhotoUnreadable("Исходное фото не читается — загрузите JPEG, PNG или WebP") from exc

    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA", "P"):
        # Прозрачный фон — белым, как у бумажной карточки, а не чёрным.
        rgba = image.convert("RGBA")
        image = Image.new("RGB", rgba.size, "white")
        image.paste(rgba, mask=rgba.getchannel("A"))
    else:
        image = image.convert("RGB")
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    out = io.BytesIO()
    image.save(out, format="JPEG", quality=92)
    return out.getvalue()
