"""Construction and cached loading of the existing multi-output model."""

from __future__ import annotations

import streamlit as st
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Model

from src.config import WEIGHTS_PATH


class ModelLoadError(RuntimeError):
    """Raised when the trained catfish model cannot be constructed."""


def build_prediction_model(base_weights: str | None = None) -> Model:
    """Recreate the architecture expected by the supplied complete checkpoint.

    The checkpoint contains the base-model weights, so constructing with
    ``None`` avoids an unnecessary ImageNet download during application start.
    ``base_weights`` remains injectable for controlled training/diagnostic use.
    """
    base = InceptionV3(weights=base_weights, include_top=False, input_shape=(224, 224, 3))
    for layer in base.layers:
        layer.trainable = False
    features = Flatten()(base.output)
    classification = Dense(64, activation="relu")(features)
    classification_output = Dense(
        3, activation="softmax", name="classification_output"
    )(classification)
    regression = Dense(64, activation="relu")(features)
    regression_output = Dense(
        3, activation="linear", name="regression_output"
    )(regression)
    return Model(base.input, [classification_output, regression_output])


@st.cache_resource(show_spinner=False)
def load_prediction_model() -> Model:
    """Build, load, and cache the trained catfish attribute model."""
    if not WEIGHTS_PATH.is_file():
        raise ModelLoadError(f"Required weight file is missing: {WEIGHTS_PATH.name}")
    try:
        model = build_prediction_model()
        model.load_weights(WEIGHTS_PATH)
        return model
    except Exception as exc:
        raise ModelLoadError("The model weights are missing or incompatible.") from exc
