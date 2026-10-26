# Plan

Implements [`spec.md`](spec.md). Every step writes its tests first, runs them to show they fail,
then writes the code and runs them again.

## Files to create or change
| File | Purpose |
|---|---|
| `requirements.txt` | `requests`, `python-dotenv`, `pytest`, `ruff` (all named in spec.md) |
| `pyproject.toml` | pytest config: `tests/` path and the `model` marker; ruff line length |
| `checker.py` | `check(receipt) -> list[str]`, behaviors 6–9 |
| `reader.py` | `parse_reply(text)` (behaviors 1–5, 10) and `read_receipt(path, model)`, the per-model reasoning table |
| `read_receipt.py` | CLI: one image in, JSON and findings out |
| `eval.py` | Reads each image in a folder once, compares with `expected.json`, prints a table with tokens |
| `tests/test_checker.py` | No-key tests for the checker |
| `tests/test_parser.py` | No-key tests for `parse_reply` |
| `tests/test_eval.py` | Model tests against `expected.json`, skipped without a key |
| `tests/conftest.py` | The `model` skip rule and a module-scoped fixture that reads each image once |
| `CHECKS.md`, `README.md` | Results and how to run |
| `my-receipts/` | Ethan's two photographs and a hand-written `expected.json` |

## Order of work
1. **Setup.** `.venv`, `requirements.txt`, `pyproject.toml`. Proof: `pytest` runs and collects 0
   tests; `ruff check .` runs.
2. **Checker.** Tests first in `tests/test_checker.py`: a receipt that adds up (receipt-01's
   numbers), a wrong subtotal, a wrong total, a discount (receipt-03), a receipt with no subtotal
   (receipt-05), and quantities greater than 1 (receipt-02). Run: they fail (no `checker.py`).
   Write `checker.py`. Run: green.
3. **Parser.** Tests first in `tests/test_parser.py`: plain JSON, JSON in prose, JSON in a code
   fence, not JSON, missing `total`, string numbers with `$`, negative discount, missing tax, a date
   that is not ISO. Run: red. Write `parse_reply` in `reader.py`. Run: green.
4. **Model call and CLI.** `read_receipt` and `read_receipt.py`. Tests first in
   `tests/test_eval.py` (merchant, date, item count, total, checker clean, per receipt) and the
   skip rule in `conftest.py`. Run without a key: skipped. Run with the key: red (no
   `read_receipt`). Write it. Run: green, or failures to explain.
5. **Eval script.** `eval.py` prints per receipt, per field PASS/FAIL, and tokens in and out.
   Run on `minimax/minimax-m3`, then with only `CHAT_MODEL=xiaomi/mimo-v2.6-flash` changed.
   Record both in `CHECKS.md`. Run `ruff check .` and record it. Commit "Receipt reader with
   tests, two models".
6. **Break the loop (lab step 4).** Ethan changes receipt-01's total to 13.96 by hand; the agent
   is told to make the failing test pass. Record what happened; Ethan restores the key.
7. **Own receipts and README.** `RECEIPT_DIR=my-receipts` on both models; README per the lab.

## Risks
- **The model's arithmetic agrees with the printed numbers even when it misread one.** The checker
  catches a misread only if it breaks a sum. The eval against `expected.json` is the second net.
- **Rounding.** Unit price × quantity can differ from the printed line by a cent
  (3 × 0.89 = 2.67 is exact here, but real receipts round). Tolerance is $0.01 on each sum;
  if a real receipt trips it, record it rather than widen the tolerance silently.
- **Discount sign** (step 3): if the model returns `-1.15` and the parser did not normalize it,
  receipt-03's total check would be off by 2.30. Behavior 5 and a parser test cover it.
- **Reasoning setting** (step 4): MiMo with reasoning on returns empty content with
  `finish_reason: length`. The per-model table defaults it off; the error message shows the
  finish reason if the table is wrong.
- **Cost and speed** (steps 4–5): calling the model once per test would read each image five
  times. The module-scoped fixture caches one read per image; `eval.py` reads each once.
- **Blast radius:** everything runs locally on seven images; a wrong step costs cents and is
  visible in the next test run.

## Proof

### Tests that run without a key (`pytest -m "not model"`)
- `tests/test_checker.py` proves the arithmetic: a correct receipt passes; a wrong subtotal, a
  wrong total, and a missing subtotal are each reported with the right amounts. On their own they
  prove the checker would catch a misread that breaks the sums, whatever model produced it.
- `tests/test_parser.py` proves a model reply becomes a receipt or a clean `ReadError`: prose,
  fences, string numbers, a negative discount, a non-ISO date, and a missing field. On their own
  they prove a bad reply cannot crash the program or slip a wrong discount sign past the checker.
- They do **not** prove the model reads the images correctly.

### The eval that needs a key (`pytest -m model`, `python eval.py`)
- Compares each image's read with `images/expected.json`: merchant (case-insensitive), date, item
  count, total within $0.01, and an empty problem list from the checker. It proves the model plus
  parser plus checker work end to end on the five course receipts, per model.
- If the model is right and `expected.json` is wrong, the eval fails and that is reported, never
  fixed by editing the key (the hook blocks it; see step 6).

## Questions asked before approval
1. **"Which tests run without the key, and what do they prove on their own?"** Answer: the checker
   and parser tests; they prove arithmetic and parsing on hand-written inputs, not reading.
   *Correction:* the first draft's Proof listed a single "tests" bullet. Split into the two
   subsections above, each saying what it does not prove.
2. **"What does the eval compare against, and what if the model is right and `expected.json` is
   wrong?"** Answer: the five fields above; a disagreement is reported and the run stops there.
   *Correction:* the first draft compared merchant by exact string, which would fail
   "MATHER DINING HALL" vs "Mather Dining Hall". Merchant is now compared case-insensitively;
   nothing else is loosened.
3. **"What could break in step 4, and how would I notice?"** Answer: MiMo's empty reply with
   reasoning on. *Correction:* added the reasoning risk and the `finish_reason` in the error.

## Subagents and parallel work
None. The steps depend on each other and the lab is small.

**Approved by:** Ethan Ambrossi, 2026-10-26
