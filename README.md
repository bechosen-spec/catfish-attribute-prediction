# Catfish Attribute Estimator

A local Streamlit application that accepts an uploaded image or webcam capture,
checks that it is a usable image containing a likely fish, and then estimates:

- growth stage: fingerling, juvenile, or adult;
- standard length in centimetres;
- total length in centimetres; and
- weight in grams.

The estimates come from the existing multi-output InceptionV3 model stored in
`InceptionV3_best_model.weights.h5`. They are decision-support estimates, not a
replacement for direct physical measurement.

## Safety features

The attribute model is a closed-set classifier, so it cannot reject unrelated
objects on its own. This application puts three gates in front of it:

1. **File validation** — limits uploads to readable JPEG or PNG files of at most
   10 MB and rejects corrupt, empty, truncated, unsupported, or decompression-bomb
   images.
2. **Quality validation** — rejects extremely small, blank, severely dark,
   severely bright, or very blurry images using deliberately conservative
   thresholds in `src/config.py`.
3. **Fish-presence validation** — a separate ImageNet-pretrained MobileNetV2
   inspects the top ten labels. The image proceeds only when fish-related
   confidence passes both configured thresholds **and the top-ranked label is
   fish-related**. Confident non-fish results are rejected; ambiguous results
   are reported as uncertain. Incidental low-ranking fish probability cannot
   override a dominant non-fish label.

Validation and presentation thresholds are centralised in `src/config.py`:

| Setting | Value | Purpose |
|---|---:|---|
| Minimum dimensions | 160 × 160 px | Reject images too small for useful detail |
| Brightness range | 8–247 | Reject severely dark or washed-out images |
| Minimum pixel standard deviation | 4 | Reject blank or near-uniform images |
| Minimum edge score | 18 | Reject severe blur while retaining ordinary photos |
| Minimum top fish probability | 0.08 | Require a meaningful fish category |
| Minimum combined fish probability | 0.12 | Require supporting fish evidence |
| Confident non-fish probability | 0.30 | Clearly reject a dominant non-fish label |
| Growth-stage warning | below 0.60 | Mark low-confidence attribute results |

The validator confirms only a **likely generic fish**. It does not reliably
identify catfish species. ImageNet classification is an additional safeguard,
not a perfect object detector, and unusual fish photographs may be rejected.

```text
Upload / camera
      │
      ▼
File and quality checks ──fail──▶ Explain rejection and stop
      │
      ▼
MobileNetV2 fish check ──no/uncertain──▶ Explain rejection and stop
      │
      ▼
Existing InceptionV3 attribute model
      │
      ▼
Growth-stage probabilities + length and weight estimates
```

## Model architecture

The attribute model preserves the architecture expected by the supplied weights:

- frozen ImageNet InceptionV3 feature extractor without its original top;
- flattened features;
- a 64-unit ReLU classification branch and three-class softmax output;
- a separate 64-unit ReLU regression branch and three linear outputs.

The original preprocessing is preserved: RGB conversion, resize to 224 × 224,
float conversion, division by 255, and a leading batch dimension. No inverse
target scaling is applied because the repository contains no evidence of one.
Negative or non-finite physical predictions are rejected instead of displayed.
Classification probabilities must be finite, stay between zero and one, and
sum to approximately one. If total length is estimated below standard length,
the interface shows a physical-plausibility warning.

Both neural networks are loaded once with `st.cache_resource`.

## Requirements and installation

Use Python 3.9–3.12. TensorFlow 2.16 does not support Python 3.13.

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The first run may download public ImageNet weights for InceptionV3 and
MobileNetV2 into the Keras cache. Later runs use that local cache. No paid API or
remote inference service is used.

The fish validator uses
[MobileNetV2 from Keras Applications](https://keras.io/api/applications/mobilenet/#mobilenetv2-function),
pretrained on ImageNet. TensorFlow/Keras is distributed under the
[Apache License 2.0](https://github.com/keras-team/keras/blob/master/LICENSE).
ImageNet has its own dataset terms; its pretrained labels and weights are used
for inference.

## Run

Ensure the trained file exists at the repository root:

```text
InceptionV3_best_model.weights.h5
```

Then start the application:

```bash
streamlit run app.py
```

Upload a JPEG or PNG image, or use the webcam control. Use one clearly visible
fish, good lighting, a sharp image, and a simple background. A side or top view
is preferable. Uploads are limited to 10 MB by both Streamlit and the
application's decoding layer.

## Tests

Tests mock neural-network inference and do not download pretrained models:

```bash
pytest -q
```

The suite covers valid/RGB image loading, bad files, small and blank images,
blur rejection, fish/non-fish/uncertain label decisions, preprocessing shape,
prediction output shapes, missing weights, and invalid physical outputs.

## Project structure

```text
app.py                         Streamlit entry point
assets/logo.jpeg               Existing application logo
InceptionV3_best_model.weights.h5
src/config.py                  Paths and named thresholds
src/analysis.py                Validation-first inference boundary
src/preprocessing.py           Safe decoding, quality checks, preprocessing
src/image_validator.py         Cached MobileNetV2 fish gate
src/model.py                   Preserved attribute-model architecture/loading
src/prediction.py              Output validation and typed results
src/ui.py                      Streamlit styling and presentation
tests/                         Fast automated tests
```

## Known limitations

This repository does not include the training dataset, training script,
validation metrics, regression-target normalisation details, independent
accuracy results, or documented out-of-distribution evaluation. Therefore the
attribute model cannot be reproduced or independently benchmarked from this
repository alone.

MobileNetV2 is an image classifier rather than a localisation detector. It can
miss small, obscured, unusual, or out-of-frame fish and may be influenced by the
background. It cannot guarantee that an accepted fish is a catfish. The
configured gates substantially reduce obvious non-fish predictions, but no
automated validator is perfect.
