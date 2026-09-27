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


def _inverse(value: float, scaler: dict, *, logarithmic: bool = False) -> float:
    raw = value * float(scaler["scale"]) + float(scaler["mean"])
    return float(np.expm1(raw) if logarithmic else raw)


def parse_outputs(outputs, *, class_names=CLASS_NAMES, scalers=None) -> PredictionResult:
    """Validate model output shapes and suppress impossible measurements."""
    if not isinstance(outputs, (list, tuple)) or len(outputs) != 4:
        raise PredictionError("The model returned an unexpected output structure.")
    classes = np.asarray(outputs[0], dtype=float)
    heads = [np.asarray(outputs[i], dtype=float) for i in range(1, 4)]
    if any(head.shape != (1, 1) for head in heads):
        raise PredictionError("The model returned unexpected prediction dimensions.")
    regression = np.asarray([head[0, 0] for head in heads], dtype=float).reshape(1, 3)
    if classes.shape != (1, 3) or regression.shape != (1, 3):
        raise PredictionError("The model returned unexpected prediction dimensions.")
    if not np.all(np.isfinite(classes)) or not np.all(np.isfinite(regression)):
        raise PredictionError("The model returned invalid numeric values.")
    if np.any(classes < 0.0) or np.any(classes > 1.0):
        raise PredictionError("The model returned invalid class probabilities.")
    if not np.isclose(float(classes[0].sum()), 1.0, atol=1e-3):
        raise PredictionError("The model returned class probabilities that do not sum to one.")
    if scalers is not None:
        regression[0] = [_inverse(regression[0, 0], scalers["standard_length_cm"]), _inverse(regression[0, 1], scalers["total_length_cm"]), _inverse(regression[0, 2], scalers["weight_g_log1p"], logarithmic=True)]
    if np.any(regression[0] < 0):
        raise PredictionError("The model produced an invalid negative physical estimate.")

    class_index = int(np.argmax(classes[0]))
    probabilities = {
        name: float(classes[0, index]) for index, name in enumerate(class_names)
    }
    return PredictionResult(
        growth_stage=class_names[class_index],
        confidence=probabilities[class_names[class_index]],
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
    return parse_outputs(outputs, class_names=getattr(model, "_catfish_class_names", CLASS_NAMES), scalers=getattr(model, "_catfish_scalers", None))
