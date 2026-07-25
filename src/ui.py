"""Reusable presentation components for the Streamlit interface."""

from __future__ import annotations

from html import escape
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

from src.image_validator import ValidationResult
from src.prediction import PredictionResult


def apply_styles() -> None:
    """Apply the aquaculture design system.

    The final selector block targets stable Streamlit ``data-testid`` attributes
    only where native controls cannot be assigned custom classes.
    """
    st.markdown(
        """
        <style>
        :root {
          --ocean: #0B4F6C;
          --aqua: #01A9D6;
          --teal: #087F8C;
          --green: #20A957;
          --ink: #102A43;
          --muted: #577381;
          --surface: #FFFFFF;
          --canvas: #F4FBFD;
          --line: #D8EBF0;
          --amber: #D97706;
          --red: #C92A2A;
        }
        html, body, [class*="css"] {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system,
            BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .stApp {
          color: var(--ink);
          background:
            radial-gradient(circle at 8% 2%, rgba(1,186,239,.10), transparent 25rem),
            radial-gradient(circle at 96% 18%, rgba(32,191,85,.08), transparent 22rem),
            var(--canvas);
        }
        .block-container {
          max-width: 1120px;
          padding: 2rem 2rem 1.5rem;
        }
        .hero {
          position: relative;
          overflow: hidden;
          display: grid;
          grid-template-columns: 136px minmax(0, 1fr);
          gap: 1.8rem;
          align-items: center;
          padding: 2rem 2.2rem;
          border-radius: 28px;
          color: #fff;
          background: linear-gradient(125deg, #083F58 0%, #087F8C 62%, #0D9975 100%);
          box-shadow: 0 18px 45px rgba(11,79,108,.20);
        }
        .hero::after {
          content: "";
          position: absolute;
          width: 270px;
          height: 270px;
          border-radius: 50%;
          right: -80px;
          top: -130px;
          border: 44px solid rgba(255,255,255,.07);
        }
        .hero-logo {
          width: 126px;
          height: 126px;
          object-fit: cover;
          border-radius: 24px;
          border: 4px solid rgba(255,255,255,.82);
          box-shadow: 0 10px 28px rgba(0,0,0,.18);
        }
        .hero-copy { position: relative; z-index: 1; }
        .hero-badge {
          display: inline-flex;
          gap: .45rem;
          align-items: center;
          padding: .38rem .72rem;
          border: 1px solid rgba(255,255,255,.35);
          border-radius: 999px;
          background: rgba(255,255,255,.14);
          font-size: .78rem;
          font-weight: 750;
          letter-spacing: .045em;
          text-transform: uppercase;
        }
        .hero h1 {
          color: #fff;
          margin: .7rem 0 .45rem;
          max-width: 780px;
          font-size: clamp(2rem, 4vw, 3.15rem);
          line-height: 1.08;
          letter-spacing: -.035em;
        }
        .hero p {
          color: rgba(255,255,255,.90);
          max-width: 720px;
          margin: 0;
          font-size: 1.05rem;
          line-height: 1.65;
        }
        .section-heading {
          margin: 2rem 0 1rem;
        }
        .section-kicker {
          color: var(--teal);
          font-size: .76rem;
          font-weight: 800;
          letter-spacing: .09em;
          text-transform: uppercase;
        }
        .section-heading h2 {
          color: var(--ink);
          margin: .2rem 0 .25rem;
          font-size: 1.5rem;
          letter-spacing: -.02em;
        }
        .section-heading p { color: var(--muted); margin: 0; line-height: 1.55; }
        .feature-grid, .steps-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: .9rem;
        }
        .feature-card, .step-card {
          min-height: 132px;
          padding: 1.15rem;
          border: 1px solid var(--line);
          border-radius: 18px;
          background: rgba(255,255,255,.88);
          box-shadow: 0 7px 24px rgba(11,79,108,.055);
        }
        .feature-icon {
          display: grid;
          place-items: center;
          width: 42px;
          height: 42px;
          margin-bottom: .75rem;
          border-radius: 13px;
          background: #E7F8FB;
          font-size: 1.25rem;
        }
        .feature-card h3, .step-card h3 {
          color: var(--ink);
          margin: 0 0 .3rem;
          font-size: .98rem;
        }
        .feature-card p, .step-card p {
          color: var(--muted);
          margin: 0;
          font-size: .88rem;
          line-height: 1.5;
        }
        .steps-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .step-card { position: relative; min-height: 116px; padding-left: 4rem; }
        .step-number {
          position: absolute;
          left: 1rem;
          top: 1rem;
          display: grid;
          place-items: center;
          width: 38px;
          height: 38px;
          border-radius: 12px;
          color: #fff;
          background: var(--ocean);
          font-weight: 800;
        }
        .guidance-strip {
          display: flex;
          flex-wrap: wrap;
          gap: .55rem;
          margin-top: .85rem;
        }
        .guide-pill {
          padding: .42rem .7rem;
          border: 1px solid #CDE8E4;
          border-radius: 999px;
          color: #176B5B;
          background: #EEFAF6;
          font-size: .8rem;
          font-weight: 650;
        }
        .input-shell {
          margin-top: 2rem;
          padding: 1.35rem 1.45rem .3rem;
          border: 1px solid var(--line);
          border-radius: 22px 22px 0 0;
          background: #fff;
          box-shadow: 0 12px 34px rgba(11,79,108,.08);
        }
        .input-shell h2 { margin: 0; color: var(--ink); font-size: 1.35rem; }
        .input-shell p { margin: .35rem 0 .85rem; color: var(--muted); }
        .privacy-note {
          display: flex;
          align-items: center;
          gap: .55rem;
          margin: .7rem 0 1rem;
          color: #326677;
          font-size: .84rem;
        }
        .preview-card {
          margin: 1rem 0 .75rem;
          padding: 1rem;
          border: 1px solid var(--line);
          border-radius: 18px;
          background: #fff;
          box-shadow: 0 8px 24px rgba(11,79,108,.055);
        }
        .preview-meta {
          display: flex;
          flex-wrap: wrap;
          justify-content: space-between;
          gap: .6rem;
          margin-bottom: .7rem;
        }
        .preview-title { color: var(--ink); font-weight: 750; }
        .meta-pills { display: flex; flex-wrap: wrap; gap: .4rem; }
        .meta-pill {
          padding: .25rem .55rem;
          border-radius: 999px;
          color: #406777;
          background: #EDF7FA;
          font-size: .75rem;
          font-weight: 650;
        }
        .state-card {
          margin: 1rem 0;
          padding: 1.1rem 1.2rem;
          border: 1px solid;
          border-radius: 17px;
        }
        .state-card h3 { margin: 0 0 .3rem; font-size: 1.05rem; }
        .state-card p { margin: 0; line-height: 1.55; }
        .state-card small { display: block; margin-top: .55rem; line-height: 1.45; }
        .state-success { color: #155E45; border-color: #A7E2CA; background: #EDFBF5; }
        .state-warning { color: #854D0E; border-color: #F4D59B; background: #FFF8E8; }
        .state-error { color: #991B1B; border-color: #F3B8B8; background: #FFF2F2; }
        .dashboard-title { margin: 1.8rem 0 .8rem; }
        .dashboard-title h2 { margin: 0; color: var(--ink); font-size: 1.55rem; }
        .dashboard-title p { margin: .25rem 0 0; color: var(--muted); }
        .metric-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: .9rem;
        }
        .metric-card {
          min-height: 154px;
          padding: 1.15rem;
          border: 1px solid var(--line);
          border-radius: 19px;
          background: #fff;
          box-shadow: 0 9px 26px rgba(11,79,108,.07);
        }
        .metric-card.stage-fingerling { border-top: 4px solid #01A9D6; }
        .metric-card.stage-juvenile { border-top: 4px solid #20A957; }
        .metric-card.stage-adult { border-top: 4px solid #0B4F6C; }
        .metric-icon { font-size: 1.35rem; }
        .metric-label { color: var(--muted); margin-top: .6rem; font-size: .8rem; font-weight: 700; }
        .metric-value {
          color: var(--ink);
          margin-top: .18rem;
          font-size: clamp(1.45rem, 2.7vw, 2rem);
          font-weight: 820;
          line-height: 1.15;
          letter-spacing: -.025em;
        }
        .metric-unit { color: var(--muted); font-size: .76rem; margin-top: .35rem; }
        .confidence-card, .interpretation-card, .disclaimer-card {
          margin-top: 1rem;
          padding: 1.15rem 1.25rem;
          border: 1px solid var(--line);
          border-radius: 18px;
          background: #fff;
        }
        .confidence-row { display:flex; justify-content:space-between; gap:1rem; align-items:center; }
        .confidence-row h3 { margin: 0; font-size: 1rem; }
        .confidence-badge {
          padding: .32rem .65rem;
          border-radius: 999px;
          color: #fff;
          background: var(--teal);
          font-size: .75rem;
          font-weight: 750;
        }
        .prob-row {
          display: grid;
          grid-template-columns: 90px 1fr 58px;
          gap: .7rem;
          align-items: center;
          margin: .65rem 0;
          color: var(--ink);
          font-size: .88rem;
        }
        .prob-track { height: 9px; overflow: hidden; border-radius: 999px; background: #E5F0F3; }
        .prob-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #01A9D6, #20A957); }
        .interpretation-card { border-left: 5px solid var(--aqua); background: #F8FDFF; }
        .interpretation-card h3, .disclaimer-card h3 { margin: 0 0 .35rem; font-size: 1rem; }
        .interpretation-card p, .disclaimer-card p { margin: 0; color: var(--muted); line-height: 1.6; }
        .disclaimer-card { border-left: 5px solid var(--ocean); margin-bottom: 1rem; }
        .empty-state {
          margin: .8rem 0 1rem;
          padding: 1.1rem;
          text-align: center;
          border: 1px dashed #A9CCD5;
          border-radius: 16px;
          color: var(--muted);
          background: #F8FCFD;
        }
        .footer {
          margin-top: 2.4rem;
          padding: 1.4rem .5rem .5rem;
          border-top: 1px solid var(--line);
          color: var(--muted);
          text-align: center;
          font-size: .82rem;
          line-height: 1.7;
        }
        .footer strong { color: var(--ocean); }

        /* Minimal Streamlit-native control theming. */
        div[data-testid="stFileUploader"] {
          padding: .5rem .8rem;
          border: 1px dashed #8BCAD8;
          border-radius: 16px;
          background: #F7FCFD;
        }
        .stButton > button {
          min-height: 2.7rem;
          border-radius: 12px;
          font-weight: 750;
          transition: transform .15s ease, box-shadow .15s ease;
        }
        .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 7px 17px rgba(11,79,108,.14); }
        div[data-testid="stImage"] img { border-radius: 14px; }
        div[data-testid="stProgress"] > div { border-radius: 999px; }

        @media (max-width: 850px) {
          .feature-grid, .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
          .steps-grid { grid-template-columns: 1fr; }
          .hero { grid-template-columns: 100px 1fr; padding: 1.6rem; }
          .hero-logo { width: 96px; height: 96px; border-radius: 19px; }
        }
        @media (max-width: 520px) {
          .block-container { padding: 1rem .85rem 1.25rem; }
          .hero { display:block; padding: 1.35rem; border-radius: 21px; }
          .hero-logo { width: 76px; height: 76px; margin-bottom: .8rem; }
          .hero h1 { font-size: 2rem; }
          .hero p { font-size: .93rem; }
          .feature-grid, .metric-grid { grid-template-columns: 1fr; }
          .feature-card { min-height: auto; }
          .input-shell { padding: 1.1rem 1rem .2rem; }
          .confidence-row { align-items:flex-start; flex-direction:column; gap:.5rem; }
          .prob-row { grid-template-columns: 72px 1fr 48px; gap:.45rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _section_heading(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="section-heading"><span class="section-kicker">{escape(kicker)}</span>'
        f"<h2>{escape(title)}</h2><p>{escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def render_hero(logo_path: Path) -> None:
    """Render the single primary page heading and logo."""
    st.markdown(
        f"""
        <section class="hero">
          <img class="hero-logo" src="data:image/jpeg;base64,{_image_base64(logo_path)}"
               alt="Catfish Attribute Estimator logo">
          <div class="hero-copy">
            <span class="hero-badge">✦ AI-powered fish analysis</span>
            <h1>Smart Catfish Growth and Attribute Prediction</h1>
            <p>Upload a clear fish image to estimate its growth stage, standard
            length, total length, and weight through a validation-first workflow.</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _image_base64(path: Path) -> str:
    import base64

    return base64.b64encode(path.read_bytes()).decode("ascii")


def render_feature_cards() -> None:
    _section_heading(
        "Built for reliable analysis",
        "From image check to useful estimates",
        "Every image passes through quality and fish-presence checks before prediction.",
    )
    features = (
        ("🛡️", "Fish validation", "Blocks unrelated images before attribute analysis."),
        ("🐟", "Growth stage", "Estimates fingerling, juvenile, or adult stage."),
        ("📐", "Physical estimates", "Predicts standard length, total length, and weight."),
        ("🔒", "Local analysis", "Runs locally without paid APIs or cloud inference."),
    )
    cards = "".join(
        f'<article class="feature-card"><div class="feature-icon">{icon}</div>'
        f"<h3>{title}</h3><p>{text}</p></article>"
        for icon, title, text in features
    )
    st.markdown(f'<div class="feature-grid">{cards}</div>', unsafe_allow_html=True)


def render_instructions() -> None:
    _section_heading(
        "Three simple steps",
        "How to analyse your fish image",
        "A clear, well-framed photograph gives the model the best chance of producing useful estimates.",
    )
    steps = (
        ("1", "Add an image", "Upload a JPEG or PNG, or take a webcam photograph."),
        ("2", "Validate the fish", "The system checks file quality and confirms a likely fish."),
        ("3", "Review estimates", "See growth stage, confidence, lengths, and weight."),
    )
    cards = "".join(
        f'<article class="step-card"><span class="step-number">{number}</span>'
        f"<h3>{title}</h3><p>{text}</p></article>"
        for number, title, text in steps
    )
    st.markdown(
        f'<div class="steps-grid">{cards}</div>'
        '<div class="guidance-strip">'
        '<span class="guide-pill">✓ One fish per image</span>'
        '<span class="guide-pill">✓ Good, even lighting</span>'
        '<span class="guide-pill">✓ Clear side view</span>'
        '<span class="guide-pill">✓ Simple background</span>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_input_header() -> None:
    st.markdown(
        '<div class="input-shell"><span class="section-kicker">Start analysis</span>'
        "<h2>Add a fish image</h2>"
        "<p>Choose an image source below. JPEG and PNG files up to 10 MB are supported.</p>"
        '<div class="privacy-note">🔒 Your image is processed by the models running with this application.</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_preview(data: bytes, filename: str) -> None:
    """Render image preview and concise metadata."""
    try:
        with Image.open(BytesIO(data)) as image:
            image_format = image.format or "Image"
            dimensions = f"{image.width} × {image.height} px"
    except Exception:
        image_format = "Unverified"
        dimensions = "Dimensions unavailable"
    file_size = _format_bytes(len(data))
    st.markdown(
        '<div class="preview-card"><div class="preview-meta">'
        '<span class="preview-title">🖼️ Selected image</span><div class="meta-pills">'
        f'<span class="meta-pill">{escape(image_format)}</span>'
        f'<span class="meta-pill">{escape(dimensions)}</span>'
        f'<span class="meta-pill">{escape(file_size)}</span>'
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.image(data, caption=filename, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _format_bytes(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / 1024:.1f} KB"


def render_empty_state() -> None:
    st.markdown(
        '<div class="empty-state">🐟 Select one clear fish image to begin. '
        "No prediction is made until validation passes.</div>",
        unsafe_allow_html=True,
    )


def render_validation_details(result: ValidationResult) -> None:
    """Render accepted, uncertain, and rejected states without colour-only meaning."""
    label = escape(result.detected_label.title())
    reason = escape(result.reason)
    if result.is_valid:
        st.markdown(
            '<div class="state-card state-success"><h3>✓ Fish validation passed</h3>'
            f"<p>Likely category: <strong>{label}</strong> · Validation confidence: "
            f"<strong>{result.confidence:.1%}</strong></p>"
            "<small>The image can proceed to attribute estimation. The validator "
            "confirms a likely fish, not specifically a catfish species.</small></div>",
            unsafe_allow_html=True,
        )
    elif result.status == "uncertain":
        st.markdown(
            '<div class="state-card state-warning"><h3>⚠ Fish presence is uncertain</h3>'
            f"<p>{reason}</p><small>Try centring one fish, improving the lighting, "
            "and using a less cluttered background.</small></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="state-card state-error"><h3>✕ Image could not be analysed</h3>'
            f"<p>{reason}</p><small>No growth stage or physical measurements were "
            "produced. Try a sharper photograph showing one fish clearly.</small></div>",
            unsafe_allow_html=True,
        )


def render_results(result: PredictionResult, warning_threshold: float) -> None:
    """Render metrics, confidence, probability bars, and interpretation."""
    stage = escape(result.growth_stage.title())
    stage_class = f"stage-{escape(result.growth_stage)}"
    st.markdown(
        '<div class="dashboard-title"><span class="section-kicker">Analysis complete</span>'
        "<h2>Estimated fish attributes</h2>"
        "<p>Review the prediction and supporting confidence information below.</p></div>",
        unsafe_allow_html=True,
    )
    metrics = (
        ("🐟", "Growth stage", stage, "Predicted life stage", stage_class),
        ("📏", "Standard length", f"{result.standard_length_cm:.2f}", "centimetres (cm)", ""),
        ("↔️", "Total length", f"{result.total_length_cm:.2f}", "centimetres (cm)", ""),
        ("⚖️", "Estimated weight", f"{result.weight_g:.2f}", "grams (g)", ""),
    )
    cards = "".join(
        f'<article class="metric-card {css_class}"><span class="metric-icon">{icon}</span>'
        f'<div class="metric-label">{label}</div><div class="metric-value">{value}</div>'
        f'<div class="metric-unit">{unit}</div></article>'
        for icon, label, value, unit, css_class in metrics
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)

    confidence_label = _confidence_label(result.confidence, warning_threshold)
    st.markdown(
        '<div class="confidence-card"><div class="confidence-row">'
        "<h3>Growth-stage confidence</h3>"
        f'<span class="confidence-badge">{confidence_label} · {result.confidence:.1%}</span>'
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.progress(
        min(max(result.confidence, 0.0), 1.0),
        text="Model confidence indicates certainty, not guaranteed correctness.",
    )

    with st.expander("View growth-stage probabilities"):
        rows = "".join(
            '<div class="prob-row">'
            f"<strong>{escape(name.title())}</strong>"
            '<div class="prob-track">'
            f'<div class="prob-fill" style="width:{max(0.0, min(probability, 1.0)) * 100:.2f}%"></div>'
            "</div>"
            f"<span>{probability:.1%}</span></div>"
            for name, probability in result.probabilities.items()
        )
        st.markdown(rows, unsafe_allow_html=True)

    if result.confidence < warning_threshold:
        st.warning(
            "This growth-stage estimate has low confidence. Try a clearer side-view photograph."
        )
    if result.total_length_cm < result.standard_length_cm:
        st.warning(
            "The estimated total length is smaller than the standard length, "
            "which is physically unusual. Verify these values by direct measurement."
        )

    st.markdown(
        '<div class="interpretation-card"><h3>💡 Result interpretation</h3>'
        f"<p>The model estimates that this fish is most likely in the "
        f"<strong>{stage.lower()}</strong> growth stage. The displayed measurements "
        "are AI-generated estimates and may differ from direct physical measurements.</p></div>",
        unsafe_allow_html=True,
    )


def _confidence_label(confidence: float, warning_threshold: float) -> str:
    if confidence >= 0.80:
        return "High confidence"
    if confidence >= warning_threshold:
        return "Moderate confidence"
    return "Low confidence"


def render_disclaimer() -> None:
    st.markdown(
        '<div class="disclaimer-card"><h3>ℹ️ Understand the limits</h3>'
        "<p>Measurements are estimates. Fish validation does not confirm catfish "
        "species, and results depend on image quality, pose, and background. "
        "Use direct physical measurement whenever precision matters.</p></div>",
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        '<footer class="footer"><strong>Catfish Attribute Estimator</strong><br>'
        "Aquaculture research and decision-support tool · Built with TensorFlow and Streamlit<br>"
        "Machine-learning estimates should be verified by direct measurement.</footer>",
        unsafe_allow_html=True,
    )
