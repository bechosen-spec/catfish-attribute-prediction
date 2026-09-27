import numpy as np
import pytest

from src.model import build_prediction_model
from src.prediction import parse_outputs


def test_efficientnet_multitask_model_has_verified_outputs():
    model = build_prediction_model(base_weights=None)
    assert model.name == "catfish_efficientnetb0_multitask"
    assert model.output_names == ["class_output", "sl_output", "tl_output", "weight_output"]
    assert [tuple(output.shape[1:]) for output in model.outputs] == [(3,), (1,), (1,), (1,)]


def test_inverse_scalers_are_applied():
    scalers = {"standard_length_cm": {"mean": 10, "scale": 2}, "total_length_cm": {"mean": 12, "scale": 2}, "weight_g_log1p": {"mean": np.log1p(100), "scale": 1}}
    result = parse_outputs([np.array([[.1, .8, .1]]), np.array([[1.]]), np.array([[2.]]), np.array([[0.]])], scalers=scalers)
    assert result.standard_length_cm == 12
    assert result.total_length_cm == 16
    assert result.weight_g == pytest.approx(100)
