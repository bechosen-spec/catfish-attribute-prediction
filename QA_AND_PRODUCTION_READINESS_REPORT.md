# QA and production readiness report

## Executive summary

**Current status: BLOCKED from production deployment.** The local development environment and automated suite have been tested. No hosting target, production database, durable private image store, deployment credentials, or deployment workflow is configured in this repository. Deployment has therefore not been attempted.

## Initial application status

- PASS — Python 3.9.6, Streamlit 1.50.0, SQLAlchemy 2.0.54, Argon2 23.1.0, TensorFlow 2.16.2 and pytest 8.4.2 are installed in `.venv`.
- PASS — Supplied InceptionV3 weights are present in the project root.
- PASS — Python 3.9 SQLAlchemy mapped-annotation compatibility was corrected previously.
- FAIL (fixed) — SQLite connections did not explicitly enable foreign-key enforcement.
- FAIL (fixed) — generated local databases and private retained images were not ignored by Git.
- BLOCKED — repository Git status is unavailable in this environment because the existing Git LFS filter cannot access its temporary directory.

## Bugs fixed

1. Enabled `PRAGMA foreign_keys=ON` on SQLite connections in `src/database.py`.
2. Added `data/` and `*.db` to `.gitignore`.
3. Added mocked persistence tests for rejected and successful experiment flows.
4. Removed the InceptionV3 ImageNet-download dependency at prediction-model startup. The supplied checkpoint was verified to load successfully with an uninitialised base architecture, confirming it contains the required weights.
5. Replaced MobileNetV2's implicit Keras download/cache behavior with explicit local checkpoint and ImageNet-label paths, SHA-256 integrity checks, and controlled failure messages. The model cannot fall back to random weights.
6. Enforced the existing `must_change_password` administrator flag in Streamlit navigation. An initial administrator now has access only to profile/password change and logout until the password is changed.

## Automated tests

- PASS — Final full suite: **40 passed, 0 failed, 0 skipped, 0 errors** (`.venv/bin/python -m pytest -q`).
- NOT TESTED — browser-driven Streamlit UI testing; no browser test harness/configuration is provided.
- PASS — The supplied InceptionV3 checkpoint loaded offline and exposed the expected `(None, 3)` classification and regression outputs.
- PASS — MobileNetV2 and the ImageNet class index loaded offline from verified local assets. Live inference ran on the three supplied sample images and a synthetic non-fish image. `adult_sample.png` and `juvenile_sample.png` were conservatively **uncertain**; `fingerling_sample.png` was **rejected for image quality**; synthetic noise was **rejected** with a 70.59% non-fish top label (`velvet`). No threshold was changed. These supplied images therefore do not establish an accepted-fish end-to-end prediction result.
- PASS (limited, non-mutating) — A local Streamlit server at `127.0.0.1:8511` rendered the welcome page and sign-in view in a browser. Navigation, branding, disclaimer, footer, username/email field, password field and sign-in button were visibly confirmed. The temporary QA server was stopped after the check.
- PASS — Isolated browser authentication QA used `/private/tmp/catfish-e2e-qa.db`: registration of an ordinary user, user login/dashboard, logout, initial administrator login restriction, administrator login, overview metrics, and registered-user table all rendered and behaved correctly. Initial admins were restricted to profile/logout until a password change was made.
- BLOCKED — browser prediction upload, successful prediction persistence, experiment history/detail, and administrator all-experiments view. No repository image passed the unchanged generic-fish gate; no legitimate replacement catfish photo is available in the repository.

## Security and model review

- PASS (code/test evidence) — Argon2 password hashes; no password values are exported or stored in session state.
- PASS (code/test evidence) — user history queries are scoped by owner id; admin role is loaded from the database, not navigation state.
- PASS (existing tests) — rejected/uncertain images do not load or invoke the attribute model.
- PASS (existing tests) — malformed, non-finite, invalid-probability, and negative prediction values are rejected.
- LIMITATION — MobileNetV2 confirms likely generic fish only; it does not identify catfish species.
- LIMITATION — supplied InceptionV3 weights lack reproducible training/evaluation data and should not be represented as independently validated.

## Sample-image validation investigation

The available standalone candidate images are only the three labelled app sample inputs. They are treated as named samples, not independently verified ground truth. `adult_sample.png` passed quality but MobileNetV2's top labels were `kite` (17.47%), `hummingbird` (10.04%), and `slug` (8.46%); `juvenile_sample.png` passed quality but was led by `ground_beetle` (17.12%) and `rhinoceros_beetle` (14.65%). Neither contains a top-ranked ImageNet fish label, so both are correctly uncertain under the conservative rule. `fingerling_sample.png` has mean brightness 251.85, above the configured 247 maximum, and is correctly rejected before classification. This is ImageNet domain mismatch plus one objective exposure failure, not an image-decoding, label-index, or threshold defect. No acceptance threshold was changed.

## Validator improvement decision

**NOT IMPLEMENTED IN PRODUCTION.** ImageNet-1K does not include a catfish/
`Clarias`/`Siluriformes` class, so MobileNetV2's narrow fish-label list cannot
be expected to recognize the intended species. An evidence-based replacement
requires an independent, licensed catfish/other-fish/non-fish dataset and a
fish/batch-grouped held-out test set. No such dataset is in this repository and
no comparative model evaluation exists. `VALIDATION_IMPROVEMENT_PLAN.md`
documents the proposed detector-plus-classifier design, data provenance rules,
and release metrics. The current file safety, quality checks, and conservative
generic-fish gate remain in place.

## Production readiness and deployment

**BLOCKED.** A persistent multi-user deployment requires a configured PostgreSQL `CATFISH_DATABASE_URL`, durable non-public `CATFISH_IMAGE_STORAGE`, administrator secret, backup/migration procedure, approved hosting account, and deployment configuration. SQLite is appropriate for local development only; deploying it to ephemeral hosting risks data loss. No deployment URL or Git release commit exists. See `DEPLOYMENT.md`.

The inspected checkout is on branch `main` at pre-existing commit `d17e2b2e`. A release commit was not created because the release gate is blocked.

## Git LFS status

- PASS — `git lfs` 3.7.1 is installed and identifies `InceptionV3_best_model.weights.h5` as its tracked object.
- PASS — `git status --short` completed when Git LFS was allowed to use its temporary metadata directory. The working tree has expected source/documentation changes and pre-existing untracked research artefacts; no model file was removed or altered.
