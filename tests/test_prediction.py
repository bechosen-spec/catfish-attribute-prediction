from pathlib import Path

import numpy as np
import pytest

import src.model as model_module
from src.model import ModelLoadError
from src.prediction import PredictionError, parse_outputs


def test_prediction_output_structure():
    result = parse_outputs(
        [np.array([[0.1, 0.7, 0.2]]), np.array([[12.5, 15.2, 210.0]])]
    )
    assert result.growth_stage == "juvenile"
    assert result.confidence == pytest.approx(0.7)
    assert result.standard_length_cm == 12.5
    assert set(result.probabilities) == {"fingerling", "juvenile", "adult"}


@pytest.mark.parametrize(
    "outputs",
    [
        [np.array([[0.2, 0.8]]), np.array([[1.0, 2.0, 3.0]])],
        [np.array([[0.2, 0.3, 0.5]]), np.array([[1.0, 2.0]])],
        np.array([[1.0, 2.0, 3.0]]),
    ],
)
def test_bad_prediction_shapes_are_rejected(outputs):
    with pytest.raises(PredictionError, match="unexpected"):
        parse_outputs(outputs)


def test_negative_regression_output_is_not_displayed():
    with pytest.raises(PredictionError, match="negative"):
        parse_outputs(
            [np.array([[0.8, 0.1, 0.1]]), np.array([[-1.0, 2.0, 3.0]])]
        )


def test_non_finite_output_is_rejected():
    with pytest.raises(PredictionError, match="invalid numeric"):
        parse_outputs(
            [np.array([[0.8, np.nan, 0.2]]), np.array([[1.0, 2.0, 3.0]])]
        )


@pytest.mark.parametrize(
    "probabilities",
    [
        np.array([[-0.1, 0.6, 0.5]]),
        np.array([[0.2, 0.2, 0.2]]),
        np.array([[1.2, 0.0, -0.2]]),
    ],
)
def test_invalid_class_probabilities_are_rejected(probabilities):
    with pytest.raises(PredictionError, match="probabilit"):
        parse_outputs([probabilities, np.array([[1.0, 2.0, 3.0]])])


def test_missing_weight_file_is_reported(monkeypatch, tmp_path):
    model_module.load_prediction_model.clear()
    monkeypatch.setattr(model_module, "WEIGHTS_PATH", Path(tmp_path / "missing.h5"))
    with pytest.raises(ModelLoadError, match="missing"):
        model_module.load_prediction_model()
