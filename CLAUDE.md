# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
Week 5 lab: a command-line program that reads a receipt photo with a vision model into JSON and
checks in plain code that the items, subtotal, discount, tax and total add up. See
[`spec.md`](spec.md) and [`plan.md`](plan.md).

## Commands
```
# setup   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# test    .venv/bin/python -m pytest            (model tests skipped without OPENROUTER_API_KEY)
# run     .venv/bin/python read_receipt.py images/receipt-01.png
# eval    .venv/bin/python eval.py [--dir images] [--model SLUG]
# lint    .venv/bin/ruff check .
```

## Conventions
- Python 3.13 in `.venv` (system `python3` is 3.9; use `.venv/bin/python`).
- Tests in `tests/test_*.py`. Model tests carry `@pytest.mark.model` and read each image once.
- No branches this week: commit to main.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.
- This is the Week 5 introductory lab. Stages assigned: intent, spec, plan,
  and tests. No branches or pull requests yet. Commit to main.
- Libraries and build tools are allowed. Name each dependency in spec.md
  under Dependencies, with the reason, before installing it; a hook blocks
  installs that spec.md does not list.
- images/ and images/expected.json are the answer key. Never edit them. If
  a test disagrees with the key, say so and stop.
- Tests live in tests/ (Python) or src/test (Java). Tests that call a model
  are marked and are skipped when no API key is set.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
- Ran `cat .env` while debugging and printed the API key into the transcript. Never read `.env`;
  check whether a key is set with `test -n "$OPENROUTER_API_KEY"`.
