"""Safe image loading, quality checks, and model preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import numpy as np
from PIL import Image, ImageFile, UnidentifiedImageError

from src.config import (
    MAX_FILE_BYTES,
    MAX_MEAN_BRIGHTNESS,
    MIN_EDGE_SCORE,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    MIN_MEAN_BRIGHTNESS,
    MIN_PIXEL_STDDEV,
    MODEL_INPUT_SIZE,
    SUPPORTED_FORMATS,
)

Image.MAX_IMAGE_PIXELS = 40_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False


class ImageValidationError(ValueError):
    """Raised when uploaded bytes are not a safe, usable image."""


@dataclass(frozen=True)
class ImageQuality:
    """Interpretable image-quality measurements."""

    width: int
    height: int
    mean_brightness: float
    pixel_stddev: float
    edge_score: float


def load_image(data: bytes) -> Image.Image:
    """Decode and fully verify a supported image from untrusted bytes."""
    if not data:
        raise ImageValidationError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ImageValidationError("The image is larger than the 10 MB limit.")
    try:
        with Image.open(BytesIO(data)) as probe:
            image_format = probe.format
            probe.verify()
        if image_format not in SUPPORTED_FORMATS:
            raise ImageValidationError("Only JPEG and PNG images are supported.")
        with Image.open(BytesIO(data)) as decoded:
            decoded.load()
            return decoded.convert("RGB")
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise ImageValidationError(
            "The file is corrupted or is not a readable JPEG or PNG image."
        ) from exc


def measure_quality(image: Image.Image) -> ImageQuality:
    """Calculate lightweight quality indicators without extra dependencies."""
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    horizontal = np.diff(gray, axis=1)
    vertical = np.diff(gray, axis=0)
    edge_score = float((np.mean(horizontal**2) + np.mean(vertical**2)) / 2.0)
    return ImageQuality(
        width=image.width,
        height=image.height,
        mean_brightness=float(gray.mean()),
        pixel_stddev=float(gray.std()),
        edge_score=edge_score,
    )


def quality_rejection_reason(quality: ImageQuality) -> str | None:
    """Return a user-facing rejection reason, or ``None`` when usable."""
    if quality.width < MIN_IMAGE_WIDTH or quality.height < MIN_IMAGE_HEIGHT:
        return "The image is too small for reliable analysis. Use an image at least 160 × 160 pixels."
    if quality.pixel_stddev < MIN_PIXEL_STDDEV:
        return "The image appears blank or contains too little visual detail."
    if quality.mean_brightness < MIN_MEAN_BRIGHTNESS:
        return "The image is too dark. Retake it in better lighting."
    if quality.mean_brightness > MAX_MEAN_BRIGHTNESS:
        return "The image is too bright or washed out. Retake it with more even lighting."
    if quality.edge_score < MIN_EDGE_SCORE:
        return "The image is too blurry or unclear for reliable analysis. Please use a sharper photograph."
    return None


def prepare_prediction_input(image: Image.Image) -> np.ndarray:
    """Match the preprocessing used by the existing trained attribute model."""
    resized = image.convert("RGB").resize(MODEL_INPUT_SIZE, Image.Resampling.BILINEAR)
    return np.expand_dims(np.asarray(resized, dtype=np.float32) / 255.0, axis=0)
