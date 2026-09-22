"""Independent fish-presence validation using ImageNet MobileNetV2."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
)
from tensorflow.keras.utils import get_file

from src.config import (
    CONFIDENT_NON_FISH_THRESHOLD,
    MIN_FISH_TOP_CONFIDENCE,
    MIN_FISH_TOTAL_CONFIDENCE,
    MOBILENET_V2_WEIGHTS_PATH,
    MOBILENET_V2_WEIGHTS_SHA256,
    MOBILENET_V2_WEIGHTS_FILENAME,
    MOBILENET_V2_WEIGHTS_ORIGIN,
    MOBILENET_V2_WEIGHTS_PATH_CONFIGURED,
    IMAGENET_CLASS_INDEX_PATH,
    IMAGENET_CLASS_INDEX_SHA256,
    IMAGENET_CLASS_INDEX_FILENAME,
    IMAGENET_CLASS_INDEX_ORIGIN,
    IMAGENET_CLASS_INDEX_PATH_CONFIGURED,
    MODEL_CACHE_DIR,
    VALIDATOR_INPUT_SIZE,
    VALIDATOR_TOP_K,
)
from src.preprocessing import (
    ImageValidationError,
    load_image,
    measure_quality,
    quality_rejection_reason,
)

FISH_LABELS = {
    "tench", "goldfish", "great_white_shark", "tiger_shark", "hammerhead",
    "electric_ray", "stingray", "barracouta", "eel", "coho", "rock_beauty",
    "anemone_fish", "sturgeon", "gar", "lionfish", "puffer",
}


class ValidationModelLoadError(RuntimeError):
    """Raised when the required, trusted fish-validator checkpoint is unavailable."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_asset(
    path: Path,
    *,
    filename: str,
    origin: str,
    expected_sha256: str,
    explicitly_configured: bool,
    asset_name: str,
) -> Path:
    """Use a checked local asset or acquire the original Keras asset with a hash."""
    if path.is_file():
        if _sha256(path) != expected_sha256:
            raise ValidationModelLoadError(f"{asset_name} failed its SHA-256 integrity check.")
        return path
    if explicitly_configured:
        raise ValidationModelLoadError(f"{asset_name} are unavailable at the configured path.")
    try:
        downloaded = Path(
            get_file(
                filename,
                origin,
                file_hash=expected_sha256,
                hash_algorithm="sha256",
                cache_dir=str(MODEL_CACHE_DIR),
                cache_subdir="models",
            )
        )
    except Exception as exc:
        raise ValidationModelLoadError(
            f"{asset_name} could not be obtained from the official Keras asset source."
        ) from exc
    if not downloaded.is_file() or _sha256(downloaded) != expected_sha256:
        raise ValidationModelLoadError(f"{asset_name} failed their SHA-256 integrity check.")
    return downloaded


def validation_weights_path() -> Path:
    """Return the original MobileNetV2 1.0/224 checkpoint with SHA-256 verification."""
    return _verified_asset(
        MOBILENET_V2_WEIGHTS_PATH,
        filename=MOBILENET_V2_WEIGHTS_FILENAME,
        origin=MOBILENET_V2_WEIGHTS_ORIGIN,
        expected_sha256=MOBILENET_V2_WEIGHTS_SHA256,
        explicitly_configured=MOBILENET_V2_WEIGHTS_PATH_CONFIGURED,
        asset_name="Fish-validation weights",
    )


def imagenet_class_index() -> dict[str, list[str]]:
    """Load the verified ImageNet class map without Keras' network fallback."""
    path = _verified_asset(
        IMAGENET_CLASS_INDEX_PATH,
        filename=IMAGENET_CLASS_INDEX_FILENAME,
        origin=IMAGENET_CLASS_INDEX_ORIGIN,
        expected_sha256=IMAGENET_CLASS_INDEX_SHA256,
        explicitly_configured=IMAGENET_CLASS_INDEX_PATH_CONFIGURED,
        asset_name="ImageNet class labels",
    )
    try:
        labels = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationModelLoadError("ImageNet class labels could not be read.") from exc
    if len(labels) != 1000 or any(str(index) not in labels for index in range(1000)):
        raise ValidationModelLoadError("ImageNet class labels have an unexpected format.")
    return labels


@dataclass(frozen=True)
class ValidationResult:
    """Structured outcome of file, quality, and fish-presence validation."""

    is_valid: bool
    is_fish: bool
    confidence: float
    detected_label: str
    reason: str
    status: str


@st.cache_resource(show_spinner=False)
def load_validation_model():
    """Load and cache the separately supplied, verified ImageNet fish validator."""
    try:
        return MobileNetV2(weights=str(validation_weights_path()), include_top=True)
    except ValidationModelLoadError:
        raise
    except Exception as exc:
        raise ValidationModelLoadError("Fish-validation weights are incompatible with this TensorFlow/Keras runtime.") from exc


def _classify(image: Image.Image, model) -> list[tuple[str, float]]:
    resized = image.resize(VALIDATOR_INPUT_SIZE, Image.Resampling.BILINEAR)
    batch = np.expand_dims(np.asarray(resized, dtype=np.float32), axis=0)
    predictions = np.asarray(model.predict(preprocess_input(batch), verbose=0), dtype=float)
    if predictions.shape != (1, 1000) or not np.all(np.isfinite(predictions)):
        raise ValidationModelLoadError("Fish validator returned an invalid prediction response.")
    labels = imagenet_class_index()
    indexes = np.argsort(predictions[0])[-VALIDATOR_TOP_K:][::-1]
    return [
        (labels[str(int(index))][1].lower().replace(" ", "_"), float(predictions[0, index]))
        for index in indexes
    ]


def interpret_labels(labels: list[tuple[str, float]]) -> ValidationResult:
    """Apply conservative, testable acceptance rules to decoded labels."""
    if not labels:
        return ValidationResult(False, False, 0.0, "unknown", "The validator returned no recognised content.", "uncertain")
    fish_matches = [(label, score) for label, score in labels if label in FISH_LABELS]
    fish_total = sum(score for _, score in fish_matches)
    best_fish = max(fish_matches, key=lambda item: item[1], default=("none", 0.0))
    top_label, top_score = labels[0]

    fish_is_top_label = top_label in FISH_LABELS
    if (
        fish_is_top_label
        and best_fish[1] >= MIN_FISH_TOP_CONFIDENCE
        and fish_total >= MIN_FISH_TOTAL_CONFIDENCE
    ):
        return ValidationResult(
            True, True, fish_total, best_fish[0].replace("_", " "),
            "A fish-related ImageNet category was detected. Validation confirms a likely fish, not specifically a catfish.",
            "accepted",
        )
    if top_score >= CONFIDENT_NON_FISH_THRESHOLD and not fish_is_top_label:
        return ValidationResult(
            False, False, top_score, top_label.replace("_", " "),
            "No fish was detected in this image. Please upload a clear photograph containing one fish.",
            "rejected",
        )
    return ValidationResult(
        False, False, fish_total, top_label.replace("_", " "),
        "We could not confidently confirm that this image contains a fish. Try another image with the fish centred and clearly visible.",
        "uncertain",
    )


def validate_image(data: bytes, model) -> ValidationResult:
    """Run all validation layers and never invoke the attribute model."""
    try:
        image = load_image(data)
    except ImageValidationError as exc:
        return ValidationResult(False, False, 0.0, "invalid image", str(exc), "rejected")
    quality_reason = quality_rejection_reason(measure_quality(image))
    if quality_reason:
        return ValidationResult(False, False, 0.0, "poor image quality", quality_reason, "rejected")
    return interpret_labels(_classify(image, model))
