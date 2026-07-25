from unittest.mock import Mock

import pytest

from src.analysis import predict_if_valid
from src.image_validator import ValidationResult


@pytest.mark.parametrize("status", ["rejected", "uncertain"])
def test_attribute_prediction_is_never_called_after_validation_failure(status):
    validate = Mock(
        return_value=ValidationResult(
            False, False, 0.0, "non-fish", "rejected", status
        )
    )
    predict = Mock(side_effect=AssertionError("attribute model must not run"))

    validation = validate(b"input", object())
    load_model = Mock(side_effect=AssertionError("attribute model must not load"))
    result = predict_if_valid(
        b"input", validation, load_model_fn=load_model, predict_fn=predict
    )

    assert result is None
    load_model.assert_not_called()
    predict.assert_not_called()


@pytest.mark.parametrize(
    "reason",
    [
        "blank",
        "too blurry",
        "corrupted",
        "unsupported",
        "no fish",
        "insufficient confidence",
    ],
)
def test_every_rejection_reason_blocks_attribute_inference(reason):
    validate = Mock(
        return_value=ValidationResult(
            False, False, 0.0, "invalid", reason, "rejected"
        )
    )
    predict = Mock()

    load_model = Mock()
    predict_if_valid(
        b"input",
        validate(b"input", object()),
        load_model_fn=load_model,
        predict_fn=predict,
    )

    load_model.assert_not_called()
    predict.assert_not_called()


def test_accepted_fish_calls_attribute_prediction_once():
    validation = ValidationResult(
        True, True, 0.8, "tench", "fish detected", "accepted"
    )
    expected_prediction = object()
    predict = Mock(return_value=expected_prediction)

    load_model = Mock(return_value="attribute")
    result = predict_if_valid(
        b"fish",
        validation,
        load_model_fn=load_model,
        predict_fn=predict,
    )

    assert result is expected_prediction
    load_model.assert_called_once_with()
    predict.assert_called_once_with(b"fish", "attribute")
