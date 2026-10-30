# Contributing

1. Fork and create a branch: `git checkout -b feat/my-change`
2. Install dev tools: `pip install -e ".[dev]"`
3. Run `ruff check .` and `pytest` before committing.
4. Open a pull request describing what changed and why.

New gestures go in `handtrack/gestures.py` and need a test in `tests/test_gestures.py`.
