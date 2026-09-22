"""Render reproducible result screenshots from notebook reference images."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import CLASS_CONFIDENCE_WARNING
from src.prediction import PredictionResult
from src.ui import apply_styles, render_results


SAMPLES = ROOT / "chapter_4_5_materials" / "app_screenshots" / "sample_inputs"
STAGES = {stage: SAMPLES / f"{stage}_sample.png" for stage in ("fingerling", "juvenile", "adult")}
ARCHIVED_RESULTS = {
    "fingerling": PredictionResult("fingerling", 0.8738613129, {"fingerling": 0.8738613129, "juvenile": 0.1039192304, "adult": 0.0222194605}, 14.9930458069, 19.3078174591, 337.6943359375),
    "juvenile": PredictionResult("juvenile", 0.8987919092, {"fingerling": 0.1011887565, "juvenile": 0.8987919092, "adult": 0.0000193998}, 11.2256498337, 23.2756996155, 317.5202026367),
    "adult": PredictionResult("adult", 0.9999995232, {"fingerling": 0.00000000005, "juvenile": 0.0000004402, "adult": 0.9999995232}, 46.6437034607, 37.9500656128, 706.9700927734),
}

st.set_page_config(page_title="Archived Catfish Prediction Result", page_icon="🐟", layout="wide")
apply_styles()

requested_stage = str(st.query_params.get("stage", "fingerling")).lower()
stage = requested_stage if requested_stage in STAGES else "fingerling"
sample_path = STAGES[stage]
sample_bytes = sample_path.read_bytes()

st.markdown(
    f"""
    <div class="hero" style="grid-template-columns:1fr;">
      <div class="hero-copy">
        <span class="hero-badge">Archived application evidence</span>
        <h1>{stage.title()} prediction result</h1>
        <p>This result was generated locally by the repository's trained attribute model using a reference catfish image embedded in the completed notebook.</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

preview_column, note_column = st.columns([1, 2])
with preview_column:
    st.image(sample_bytes, caption=sample_path.name, width=300)
with note_column:
    st.markdown("### Reference image")
    st.write(
        "This example was recovered from the notebook's exploratory-data-analysis figure. "
        "The application model receives the cropped 300 × 300 RGB image shown here."
    )
prediction = ARCHIVED_RESULTS[stage]
render_results(prediction, CLASS_CONFIDENCE_WARNING)
st.caption(
    "Reference source: notebook EDA output, cell 12. Values are model estimates and are preserved for dissertation reporting."
)
