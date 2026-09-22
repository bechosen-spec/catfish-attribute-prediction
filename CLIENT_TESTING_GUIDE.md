# Client testing guide

## Access

This release is for controlled client testing, not unrestricted production use.
There is no hosted URL in this repository. To run locally, follow the setup in
the README, ensure both local validator assets are configured, then start:

```bash
streamlit run app.py
```

Use a fresh local database or a dedicated testing database. Do not test against
production accounts or records.

### Streamlit Community Cloud prototype

The client-testing deployment uses the default SQLite file at `data/catfish.db`.
In the Streamlit Cloud app's **Settings → Secrets**, remove
`CATFISH_DATABASE_URL` completely and reboot the app. Do not add PostgreSQL,
Neon, Supabase, Railway, or other external database credentials for this
prototype. Cloud-local SQLite files are disposable: they can disappear after a
restart, redeploy, or instance move. Use only test accounts and test images.

An operator must create the administrator in the same running SQLite data
directory. For the deployed disposable demo, set both Streamlit Secrets below;
the app creates `admin` once when its SQLite file is empty:

```toml
CATFISH_ADMIN_EMAIL = "admin@example.com"
CATFISH_ADMIN_INITIAL_PASSWORD = "a-strong-unique-initial-password"
```

The account is not recreated, promoted, or password-reset after subsequent
restarts. The first successful sign-in requires a password change before the
administrator dashboard is available. For local use, `scripts/init_admin.py`
remains available. Cloud-local SQLite can still be lost after an instance move,
so retain only disposable test data.

## Using the application

1. Select **Create account** and enter your name, username, email, and a
   password of at least eight characters. Public registration creates ordinary
   user accounts only.
2. Select **Sign in** and use either your username or email plus password.
3. From **New prediction**, upload a JPEG/PNG image or use the webcam input.
   Choose whether the source image may be retained privately with the experiment.
4. Read the validation feedback. Only accepted images reach the attribute
   model. A successful result displays life stage, standard length, total
   length, and weight as model-generated estimates.
5. Open **Experiment history** to view only your own saved experiments and
   their validation/prediction details.
6. Use **My profile** to edit your name/email, change your password, or log out.

## Administrator access

An administrator must be created explicitly by the system operator using
`scripts/init_admin.py` and a secret environment variable. Administrators sign
in through the normal form. The first sign-in requires a password change before
the administrator dashboard is available. Admin pages show aggregate statistics,
registered users, all stored experiments, analytics, and audit logs.

## Known limitations

- Image validation is deliberately conservative. It uses an ImageNet generic
  fish gate; it does **not** reliably recognize catfish. Genuine catfish images
  may be rejected or marked uncertain.
- The attribute results are decision-support estimates, not direct physical
  measurements or scientifically validated accuracy claims.
- The current repository does not include a validated dedicated catfish
  validator or a representative, independently labelled test set. See
  `VALIDATION_IMPROVEMENT_PLAN.md`.

## Reporting a problem

Record the page, time, browser/operating system, whether the image was upload
or webcam input, validation message, and non-sensitive reproduction steps. Do
not send passwords, database files, private images, or personal account data in
bug reports. For an incorrect or rejected image, obtain consent before sharing
the image with the project team.
