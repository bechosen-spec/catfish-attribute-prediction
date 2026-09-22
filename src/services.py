"""Experiment persistence; this layer preserves the validation-before-inference boundary."""
from __future__ import annotations
import json, time, uuid
from pathlib import Path
from sqlalchemy import func, select
from src.database import Experiment, ImageValidationResult, ModelVersion, PredictionResultRecord, User, utcnow
from src.config import PRIVATE_IMAGE_DIR
from src.image_validator import validate_image
from src.analysis import predict_if_valid

MODEL_IDENTIFIER = "inceptionv3-multitask-supplied-weights"

def _model_version(session):
    item = session.scalar(select(ModelVersion).where(ModelVersion.identifier == MODEL_IDENTIFIER))
    if not item:
        item = ModelVersion(identifier=MODEL_IDENTIFIER, description="Supplied InceptionV3 multi-output weights; no independent deployment metrics available.")
        session.add(item); session.flush()
    return item

def run_experiment(session, user_id, data, *, validator, load_model_fn, predict_fn, retain_image=False):
    started = time.perf_counter(); exp = Experiment(user_id=user_id); session.add(exp); session.flush()
    validation = validate_image(data, validator)
    exp.validation = ImageValidationResult(is_valid=validation.is_valid, is_fish=validation.is_fish, confidence=validation.confidence, detected_label=validation.detected_label, reason=validation.reason, status=validation.status)
    if not validation.is_valid:
        exp.status = "REJECTED"; exp.processing_ms = round((time.perf_counter()-started)*1000); session.flush(); return exp, validation, None
    try:
        prediction = predict_if_valid(data, validation, load_model_fn=load_model_fn, predict_fn=predict_fn)
        exp.prediction = PredictionResultRecord(experiment_id=exp.id, model_version_id=_model_version(session).id, growth_stage=prediction.growth_stage, confidence=prediction.confidence, probabilities_json=json.dumps(prediction.probabilities), standard_length_cm=prediction.standard_length_cm, total_length_cm=prediction.total_length_cm, weight_g=prediction.weight_g)
        exp.status = "SUCCESS"
        if retain_image:
            store = PRIVATE_IMAGE_DIR; store.mkdir(parents=True, exist_ok=True)
            target = store / f"{uuid.uuid4().hex}.bin"; target.write_bytes(data); exp.image_path = str(target)
        exp.processing_ms = round((time.perf_counter()-started)*1000); session.flush(); return exp, validation, prediction
    except Exception as exc:
        # Keep the failed experiment and its validation result; never invent outputs.
        exp.status = "FAILED"; exp.processing_ms = round((time.perf_counter()-started)*1000); session.flush()
        return exp, validation, None

def user_experiments(session, user_id):
    return session.scalars(select(Experiment).where(Experiment.user_id == user_id).order_by(Experiment.submitted_at.desc())).all()

def admin_stats(session):
    today = utcnow().date()
    active_since = utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - __import__('datetime').timedelta(days=30)
    return {"users": session.scalar(select(func.count(User.id))), "experiments": session.scalar(select(func.count(Experiment.id))), "successful": session.scalar(select(func.count(Experiment.id)).where(Experiment.status == "SUCCESS")), "unsuccessful": session.scalar(select(func.count(Experiment.id)).where(Experiment.status != "SUCCESS")), "today": session.scalar(select(func.count(Experiment.id)).where(Experiment.submitted_at >= utcnow().replace(hour=0, minute=0, second=0, microsecond=0))), "active": session.scalar(select(func.count(User.id)).where(User.last_login_at >= active_since))}
