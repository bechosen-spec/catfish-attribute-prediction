"""Persistence tests using mocked inference; no neural-network download is needed."""
from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.services as services
from src.database import Base
from src.image_validator import ValidationResult
from src.prediction import PredictionResult


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    value = sessionmaker(bind=engine)()
    yield value
    value.close()


def _user(session):
    from src.auth import register
    user = register(session, "Test User", "tester", "test@example.com", "long-password", "long-password")
    session.commit()
    return user


def test_rejected_submission_is_saved_without_loading_attribute_model(session, monkeypatch):
    user = _user(session)
    rejected = ValidationResult(False, False, 0.0, "invalid", "bad image", "rejected")
    monkeypatch.setattr(services, "validate_image", Mock(return_value=rejected))
    load_model = Mock(side_effect=AssertionError("must not load"))
    experiment, validation, prediction = services.run_experiment(
        session, user.id, b"bad", validator=object(), load_model_fn=load_model, predict_fn=Mock()
    )
    session.commit()
    assert experiment.status == "REJECTED"
    assert experiment.validation.reason == "bad image"
    assert prediction is None
    load_model.assert_not_called()


def test_successful_submission_persists_prediction_and_model_version(session, monkeypatch):
    user = _user(session)
    accepted = ValidationResult(True, True, 0.8, "tench", "accepted", "accepted")
    result = PredictionResult("juvenile", 0.7, {"fingerling": 0.1, "juvenile": 0.7, "adult": 0.2}, 12.0, 15.0, 200.0)
    monkeypatch.setattr(services, "validate_image", Mock(return_value=accepted))
    experiment, _, prediction = services.run_experiment(
        session, user.id, b"fish", validator=object(), load_model_fn=Mock(return_value=object()), predict_fn=Mock(return_value=result)
    )
    session.commit()
    assert experiment.status == "SUCCESS"
    assert prediction == result
    assert experiment.prediction.growth_stage == "juvenile"
    assert experiment.prediction.model_version.identifier == services.MODEL_IDENTIFIER
