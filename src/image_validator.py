"""Independent fish-presence validation using ImageNet MobileNetV2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import streamlit as st
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    decode_predictions,
    preprocess_input,
)

from src.config import (
    CONFIDENT_NON_FISH_THRESHOLD,
    MIN_FISH_TOP_CONFIDENCE,
    MIN_FISH_TOTAL_CONFIDENCE,
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
    """Load and cache the separate ImageNet fish validator."""
    return MobileNetV2(weights="imagenet", include_top=True)


def _classify(image: Image.Image, model) -> list[tuple[str, float]]:
    resized = image.resize(VALIDATOR_INPUT_SIZE, Image.Resampling.BILINEAR)
    batch = np.expand_dims(np.asarray(resized, dtype=np.float32), axis=0)
    predictions = model.predict(preprocess_input(batch), verbose=0)
    decoded = decode_predictions(predictions, top=VALIDATOR_TOP_K)[0]
    return [(label.lower().replace(" ", "_"), float(score)) for _, label, score in decoded]


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
