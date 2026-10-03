from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from src.preprocessing import (
    ImageValidationError,
    load_image,
    measure_quality,
    prepare_prediction_input,
    quality_rejection_reason,
)


def image_bytes(mode="RGB", size=(240, 200), color=(30, 120, 180), fmt="PNG"):
    image = Image.new(mode, size, color=color)
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


def test_valid_image_is_loaded_as_rgb():
    image = load_image(image_bytes("L", color=100))
    assert image.mode == "RGB"
    assert image.size == (240, 200)


def test_invalid_file_is_rejected():
    with pytest.raises(ImageValidationError, match="corrupted|readable"):
        load_image(b"not an image")


def test_very_small_image_is_rejected():
    quality = measure_quality(load_image(image_bytes(size=(80, 80))))
    assert "too small" in quality_rejection_reason(quality)


def test_blank_image_is_rejected():
    quality = measure_quality(load_image(image_bytes(color=(127, 127, 127))))
    assert "blank" in quality_rejection_reason(quality)


def test_blurry_low_detail_gradient_is_rejected():
    values = np.tile(np.linspace(80, 170, 240, dtype=np.uint8), (200, 1))
    image = Image.fromarray(values).convert("RGB")
    quality = measure_quality(image)
    assert "blurry" in quality_rejection_reason(quality)


def test_prediction_preprocessing_shape_and_range():
    batch = prepare_prediction_input(load_image(image_bytes(color=(255, 0, 0))))
    assert batch.shape == (1, 224, 224, 3)
    assert batch.dtype == np.float32
    assert batch.min() == 0.0
    assert batch.max() == 1.0
