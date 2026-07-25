"""Streamlit entry point for the catfish attribute estimator."""

from __future__ import annotations

import hashlib
import logging

import streamlit as st

from src.analysis import predict_if_valid
from src.config import APP_TITLE, CLASS_CONFIDENCE_WARNING, LOGO_PATH
from src.image_validator import load_validation_model, validate_image
from src.model import ModelLoadError, load_prediction_model
from src.prediction import PredictionError, predict_attributes
from src.ui import (
    apply_styles,
    render_disclaimer,
    render_empty_state,
    render_feature_cards,
    render_footer,
    render_hero,
    render_input_header,
    render_instructions,
    render_preview,
    render_results,
    render_validation_details,
)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def _clear_analysis() -> None:
    """Clear the selected widget and all derived session results."""
    st.session_state.widget_epoch += 1
    st.session_state.analysis_digest = None
    st.session_state.validation_result = None
    st.session_state.prediction_result = None
    st.session_state.analysis_error = None


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_styles()

for key, default in {
    "widget_epoch": 0,
    "analysis_digest": None,
    "validation_result": None,
    "prediction_result": None,
    "analysis_error": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

render_hero(LOGO_PATH)
render_feature_cards()
render_instructions()
render_input_header()

source = st.radio(
    "Choose image source",
    ("📤 Upload image", "📷 Use webcam"),
    horizontal=True,
    key=f"image_source_{st.session_state.widget_epoch}",
    help="Choose one source. You can reset and switch at any time.",
)

if source == "📤 Upload image":
    image_file = st.file_uploader(
        "Upload a clear JPEG or PNG image",
        type=("jpg", "jpeg", "png"),
        key=f"upload_{st.session_state.widget_epoch}",
        help="Maximum file size: 10 MB.",
    )
else:
    image_file = st.camera_input(
        "Take a clear fish photograph",
        key=f"camera_{st.session_state.widget_epoch}",
    )

if image_file is None:
    render_empty_state()
else:
    raw_bytes = image_file.getvalue()
    filename = getattr(image_file, "name", "Captured fish image")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if st.session_state.analysis_digest != digest:
        st.session_state.analysis_digest = digest
        st.session_state.validation_result = None
        st.session_state.prediction_result = None
        st.session_state.analysis_error = None

    render_preview(raw_bytes, filename)
    action_col, reset_col = st.columns([3, 1])
    with action_col:
        analyse = st.button(
            "✨ Analyse image",
            type="primary",
            use_container_width=True,
            help="Validate the fish and estimate its attributes.",
        )
    with reset_col:
        st.button(
            "↻ Reset",
            use_container_width=True,
            on_click=_clear_analysis,
            help="Remove this image and start again.",
        )

    if analyse:
        try:
            with st.status("Analysing your image…", expanded=True) as status:
                st.write("📖 Reading the uploaded image")
                progress = st.progress(0.15)
                st.write("🔎 Checking image quality and confirming fish presence")
                validator = load_validation_model()
                validation = validate_image(raw_bytes, validator)
                st.session_state.validation_result = validation
                progress.progress(0.65)

                if not validation.is_valid:
                    st.session_state.prediction_result = None
                    status.update(
                        label="Image validation finished",
                        state="error" if validation.status == "rejected" else "complete",
                        expanded=False,
                    )
                else:
                    st.write("📐 Estimating growth stage and physical attributes")
                    prediction = predict_if_valid(
                        raw_bytes,
                        validation,
                        load_model_fn=load_prediction_model,
                        predict_fn=predict_attributes,
                    )
                    st.session_state.prediction_result = prediction
                    progress.progress(1.0)
                    st.write("✓ Preparing your results")
                    status.update(
                        label="Analysis complete",
                        state="complete",
                        expanded=False,
                    )
        except ModelLoadError:
            LOGGER.exception("The catfish prediction model failed to load")
            st.session_state.analysis_error = (
                "The prediction model is temporarily unavailable. Confirm that "
                "the trained model file is present, then try again."
            )
        except PredictionError as exc:
            LOGGER.warning("Prediction rejected: %s", exc)
            st.session_state.analysis_error = (
                "The system could not produce reliable measurements from this image. "
                "Please try another clear photograph."
            )
        except Exception:
            LOGGER.exception("Unexpected analysis failure")
            st.session_state.analysis_error = (
                "Something went wrong while analysing the image. Please reset and try again."
            )

    if st.session_state.analysis_error:
        st.error(st.session_state.analysis_error)
    validation = st.session_state.validation_result
    prediction = st.session_state.prediction_result
    if validation is not None:
        render_validation_details(validation)
    if prediction is not None:
        render_results(prediction, CLASS_CONFIDENCE_WARNING)

render_disclaimer()
render_footer()
