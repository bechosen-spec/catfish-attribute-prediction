"""Central application configuration."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = Path(os.getenv("CATFISH_DATA_DIR", ROOT_DIR / "data"))
SQLITE_DATABASE_PATH = DATA_DIR / "catfish.db"
PRIVATE_IMAGE_DIR = DATA_DIR / "private_images"
LOGO_PATH = ASSETS_DIR / "logo.jpeg"
WEIGHTS_PATH = ROOT_DIR / "InceptionV3_best_model.weights.h5"

APP_TITLE = "Catfish Attribute Estimator"
MODEL_INPUT_SIZE = (224, 224)
CLASS_NAMES = ("fingerling", "juvenile", "adult")

SUPPORTED_FORMATS = {"JPEG", "PNG"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MIN_IMAGE_WIDTH = 160
MIN_IMAGE_HEIGHT = 160
MIN_MEAN_BRIGHTNESS = 8.0
MAX_MEAN_BRIGHTNESS = 247.0
MIN_PIXEL_STDDEV = 4.0
MIN_EDGE_SCORE = 18.0

VALIDATOR_INPUT_SIZE = (224, 224)
VALIDATOR_TOP_K = 10
MOBILENET_V2_WEIGHTS_FILENAME = "mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5"
# Official Keras MobileNetV2 ImageNet top-classifier checkpoint used by TF 2.16.
MOBILENET_V2_WEIGHTS_SHA256 = "3e195a2857356cfc092cbbb460beb2a5bce279015d7792598b8d3d9e451902e3"
MOBILENET_V2_WEIGHTS_PATH = Path(
    os.getenv(
        "CATFISH_MOBILENET_WEIGHTS_PATH",
        Path.home() / ".keras" / "models" / MOBILENET_V2_WEIGHTS_FILENAME,
    )
)
IMAGENET_CLASS_INDEX_FILENAME = "imagenet_class_index.json"
IMAGENET_CLASS_INDEX_SHA256 = "a1e7a966a1f601d39e4b43e119b3e7dd4a2ad3ea08cf69847cbaf021013767bc"
IMAGENET_CLASS_INDEX_PATH = Path(
    os.getenv(
        "CATFISH_IMAGENET_CLASS_INDEX_PATH",
        Path.home() / ".keras" / "models" / IMAGENET_CLASS_INDEX_FILENAME,
    )
)
MIN_FISH_TOP_CONFIDENCE = 0.08
MIN_FISH_TOTAL_CONFIDENCE = 0.12
CONFIDENT_NON_FISH_THRESHOLD = 0.30
CLASS_CONFIDENCE_WARNING = 0.60
