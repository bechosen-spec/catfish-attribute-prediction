"""Safe extraction of classification and regression predictions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.config import CLASS_NAMES
from src.preprocessing import ImageValidationError, load_image, prepare_prediction_input


class PredictionError(RuntimeError):
    """Raised when a model response is malformed or physically invalid."""


@dataclass(frozen=True)
class PredictionResult:
    growth_stage: str
    confidence: float
    probabilities: dict[str, float]
    standard_length_cm: float
    total_length_cm: float
    weight_g: float


def parse_outputs(outputs) -> PredictionResult:
    """Validate model output shapes and suppress impossible measurements."""
    if not isinstance(outputs, (list, tuple)) or len(outputs) != 2:
        raise PredictionError("The model returned an unexpected output structure.")
    classes = np.asarray(outputs[0], dtype=float)
    regression = np.asarray(outputs[1], dtype=float)
    if classes.shape != (1, 3) or regression.shape != (1, 3):
        raise PredictionError("The model returned unexpected prediction dimensions.")
    if not np.all(np.isfinite(classes)) or not np.all(np.isfinite(regression)):
        raise PredictionError("The model returned invalid numeric values.")
    if np.any(classes < 0.0) or np.any(classes > 1.0):
        raise PredictionError("The model returned invalid class probabilities.")
    if not np.isclose(float(classes[0].sum()), 1.0, atol=1e-3):
        raise PredictionError("The model returned class probabilities that do not sum to one.")
    if np.any(regression[0] < 0):
        raise PredictionError("The model produced an invalid negative physical estimate.")

    class_index = int(np.argmax(classes[0]))
    probabilities = {
        name: float(classes[0, index]) for index, name in enumerate(CLASS_NAMES)
    }
    return PredictionResult(
        growth_stage=CLASS_NAMES[class_index],
        confidence=probabilities[CLASS_NAMES[class_index]],
        probabilities=probabilities,
        standard_length_cm=float(regression[0, 0]),
        total_length_cm=float(regression[0, 1]),
        weight_g=float(regression[0, 2]),
    )


def predict_attributes(data: bytes, model) -> PredictionResult:
    """Run the trained model after upstream fish validation has succeeded."""
    try:
        image = load_image(data)
    except ImageValidationError as exc:
        raise PredictionError(str(exc)) from exc
    outputs = model.predict(prepare_prediction_input(image), verbose=0)
    return parse_outputs(outputs)
