# Client-testing deployment requirements

This repository's client-testing configuration uses local SQLite only. It is not a production deployment plan.

Before release, provision:

1. Python 3.9–3.12, TensorFlow 2.16, and dependencies from `requirements.txt`.
2. No `CATFISH_DATABASE_URL` secret. Remove it from Streamlit Cloud Secrets if previously configured.
3. A complete verified `artifacts/efficientnetb0_multitask` bundle, supplied via
   authorized storage or `CATFISH_ARTIFACT_DIR`.
4. Internet egress on first inference so the verified MobileNetV2 and ImageNet
   class-index assets can be acquired from the official Keras/TensorFlow URLs.
   Alternatively, pre-stage their verified copies and set:

   ```bash
   CATFISH_MOBILENET_WEIGHTS_PATH=/secure/models/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5
   CATFISH_IMAGENET_CLASS_INDEX_PATH=/secure/models/imagenet_class_index.json
   ```

5. A secret `CATFISH_ADMIN_INITIAL_PASSWORD`, used once with `python scripts/init_admin.py` in the same local data directory as the app.

The default database is `data/catfish.db` and retained images are in `data/private_images`; both are ignored by Git. Streamlit Community Cloud local disk is ephemeral, so accounts, administrator setup, experiments, and retained images can be lost on restart, redeploy, or instance move. Use only disposable test data. The host must allow sufficient memory/disk for TensorFlow and the EfficientNetB0 artefact bundle.

## EfficientNetB0 artefact configuration

Deploy the complete `artifacts/efficientnetb0_multitask` bundle from an authorized persistent store (or set `CATFISH_ARTIFACT_DIR`). Keep `model.keras` out of ordinary Git; verify the manifest SHA-256 after transfer. The application will fail clearly if this bundle is unavailable and will never retrain on startup.
