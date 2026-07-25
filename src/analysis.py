"""Application-level orchestration that enforces the validation boundary."""

from __future__ import annotations

from typing import Callable

from src.image_validator import ValidationResult
from src.prediction import PredictionResult


def predict_if_valid(
    data: bytes,
    validation: ValidationResult,
    *,
    load_model_fn: Callable[[], object],
    predict_fn: Callable[[bytes, object], PredictionResult],
) -> PredictionResult | None:
    """Load and run the attribute model only after fish validation accepts."""
    if not validation.is_valid:
        return None
    return predict_fn(data, load_model_fn())
