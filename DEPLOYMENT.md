# Production deployment requirements

This repository has no configured hosting target. Do not deploy its default SQLite database to ephemeral hosting.

Before release, provision:

1. Python 3.9–3.12, TensorFlow 2.16, and dependencies from `requirements.txt`.
2. PostgreSQL and set `CATFISH_DATABASE_URL` to its SQLAlchemy connection URL.
3. A durable, non-public image directory and set `CATFISH_IMAGE_STORAGE`; authorize image reads for the experiment owner or an administrator only.
4. The supplied `InceptionV3_best_model.weights.h5` file in the application root.
5. The verified MobileNetV2 and ImageNet class-index assets, then set:

   ```bash
   CATFISH_MOBILENET_WEIGHTS_PATH=/secure/models/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5
   CATFISH_IMAGENET_CLASS_INDEX_PATH=/secure/models/imagenet_class_index.json
   ```

6. A secret `CATFISH_ADMIN_INITIAL_PASSWORD`, used once with `python scripts/init_admin.py` after a verified database backup/migration procedure.

Run `alembic upgrade head` as the deploy user before starting Streamlit. Configure host-provided secret management; do not place values in the repository. Back up PostgreSQL and retained images before each migration or release. The host must allow sufficient memory/disk for TensorFlow and the ~159 MB supplied checkpoint.
