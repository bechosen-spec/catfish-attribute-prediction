"""Construction and cached loading of the EfficientNetB0 multitask model."""

from __future__ import annotations

import hashlib
import json
import streamlit as st
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.models import Model, load_model

from src.config import CLASS_NAMES, CLASS_NAMES_PATH, MANIFEST_PATH, MODEL_PATH, PREPROCESSING_PATH, SCALERS_PATH


class ModelLoadError(RuntimeError):
    """Raised when the trained catfish model cannot be constructed."""


def build_prediction_model(base_weights: str | None = "imagenet", *, augmentation: bool = False) -> Model:
    """Build the verified shared-backbone EfficientNetB0 architecture."""
    inputs = layers.Input((224, 224, 3), name="image_input")
    x = inputs
    if augmentation:
        x = layers.RandomFlip("horizontal")(x)
        x = layers.RandomRotation(0.045)(x)
        x = layers.RandomTranslation(0.05, 0.05)(x)
        x = layers.RandomZoom(0.08, 0.08)(x)
        x = layers.RandomContrast(0.08)(x)
        x = layers.GaussianNoise(0.02)(x)
    backbone = EfficientNetB0(include_top=False, weights=base_weights, input_shape=(224, 224, 3), name="efficientnetb0_backbone")
    backbone.trainable = False
    x = backbone(x, training=False)
    x = layers.GlobalAveragePooling2D(name="head_global_average_pooling")(x)
    x = layers.BatchNormalization(name="head_batch_normalization")(x)
    x = layers.Dropout(0.35, name="head_dropout")(x)
    x = layers.Dense(192, activation="swish", name="head_dense")(x)
    class_output = layers.Dense(3, activation="softmax", dtype="float32", name="class_output")(layers.Dropout(0.2)(x))
    outputs = [class_output]
    for name in ("sl_output", "tl_output", "weight_output"):
        outputs.append(layers.Dense(1, dtype="float32", name=name)(layers.Dense(64, activation="swish")(x)))
    return Model(inputs, outputs, name="catfish_efficientnetb0_multitask")


def _read_json(path):
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelLoadError(f"Required EfficientNetB0 artefact is unreadable: {path.name}") from exc


def _load_artifacts() -> tuple[list[str], dict]:
    required = (MODEL_PATH, CLASS_NAMES_PATH, SCALERS_PATH, PREPROCESSING_PATH, MANIFEST_PATH)
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise ModelLoadError("EfficientNetB0 model artefact is not configured. Run `python -m scripts.train_efficientnet --dataset-root ...` and deploy the complete artefacts/efficientnetb0_multitask bundle. Missing: " + ", ".join(missing))
    names, scalers, preprocessing, manifest = (_read_json(CLASS_NAMES_PATH), _read_json(SCALERS_PATH), _read_json(PREPROCESSING_PATH), _read_json(MANIFEST_PATH))
    if names != list(CLASS_NAMES) or preprocessing.get("input_size") != [224, 224] or preprocessing.get("input_range") != "0..255":
        raise ModelLoadError("EfficientNetB0 artefact metadata is incompatible with this application.")
    if set(scalers) != {"standard_length_cm", "total_length_cm", "weight_g_log1p"}:
        raise ModelLoadError("EfficientNetB0 biometric scaler metadata is incomplete.")
    expected = manifest.get("model_sha256")
    if not isinstance(expected, str) or hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() != expected:
        raise ModelLoadError("EfficientNetB0 model checksum verification failed.")
    return names, scalers


@st.cache_resource(show_spinner=False)
def load_prediction_model() -> Model:
    """Load and cache a verified complete EfficientNetB0 artefact; never train."""
    try:
        names, scalers = _load_artifacts()
        model = load_model(MODEL_PATH, compile=False)
        if model.output_names != ["class_output", "sl_output", "tl_output", "weight_output"]:
            raise ValueError("unexpected output names")
        model._catfish_class_names = tuple(names)
        model._catfish_scalers = scalers
        return model
    except Exception as exc:
        if isinstance(exc, ModelLoadError):
            raise
        raise ModelLoadError("The EfficientNetB0 model is corrupted or incompatible.") from exc
