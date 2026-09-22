# Test report

## Added coverage targets

The existing tests continue to cover preprocessing, the fish gate, validation-before-inference, malformed prediction outputs, and missing weights. The new persistence/authentication layer is designed for tests covering registration validation, duplicate accounts, login/disabled accounts, ownership-scoped histories, experiment persistence, and administrator statistics.

## Execution status

At implementation time, `pytest` was not installed in the active shell (`command not found: pytest`), so the full test suite has **not** been claimed as passing. Install the requirements into a Python 3.9–3.12 virtual environment, then run `pytest -q`.

The implementation should also be exercised manually with a fresh SQLite database, an initialized administrator, a rejected upload, and a successful fish upload when model dependencies/weights are available.
