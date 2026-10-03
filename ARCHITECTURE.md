# Architecture

`app.py` is the Streamlit composition layer. It obtains the authenticated account from server-side database lookup using only a session user id; it never trusts a UI role value. Public registration always assigns `USER`. Admin views check the persisted `User.role` on every rerun.

Authentication is implemented in `src/auth.py`. It validates registration fields and stores Argon2 password hashes. Login accepts username or email, rejects disabled accounts, and has a five-attempt browser-session limiter. Password changes require current-password verification.

The prediction pipeline is deliberately unchanged: `src.preprocessing` validates safe JPEG/PNG decoding and quality; `src.image_validator` runs the MobileNetV2 generic-fish gate; only accepted `ValidationResult`s reach `src.analysis.predict_if_valid`, which loads the InceptionV3 attribute model. `src/services.run_experiment` records the validation record first, stores a rejection without loading the attribute model, and records a prediction only after successful output validation.

Images are not retained unless the user explicitly selects retention. When selected, a randomly named file is written to `CATFISH_IMAGE_STORAGE` (default `data/private_images`), outside a public static directory; database rows hold only the path. Future image-serving code must authorize either the owner or an administrator before reading it.

Alembic metadata is in `migrations/`; the initial migration is `0001_initial_schema`. Local first-run creation is also supported by `init_database()` for an easy standalone Streamlit experience.
