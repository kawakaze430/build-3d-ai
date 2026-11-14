"""Decode bounded uploads and remove metadata before storing model input."""
from __future__ import annotations

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 16_000_000


def normalize_image(data: bytes) -> bytes:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image must be between 1 byte and 10 MiB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Only PNG, JPEG and WEBP images are supported")
                if image.width * image.height > MAX_PIXELS:
                    raise ValueError("Image exceeds 16 million pixels")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Animated images are not supported")
                image.load()
                output = io.BytesIO()
                converted = ImageOps.exif_transpose(image).convert("RGBA")
                # A fresh image drops info/EXIF/ICC/text inherited by convert().
                Image.frombytes("RGBA", converted.size, converted.tobytes()).save(output, format="PNG")
                normalized = output.getvalue()
                if len(normalized) > MAX_IMAGE_BYTES:
                    raise ValueError("Decoded image exceeds storage limit")
                return normalized
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("Image cannot be safely decoded") from exc
