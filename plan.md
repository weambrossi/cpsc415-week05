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

---

## Week 6

Implements the "Week 6: image set" section of [`spec.md`](spec.md) (components 4 and 5,
behaviors 9–20). Same rule: tests first, run red, then the code, run green, stop after each step.

### Files to create or change
| File | Purpose |
|---|---|
| `week06/prompts.json` | Five creature prompts: name, prompt, seed (6101–6105), requirements, expected name text |
| `week06/checklist.py` | Plain code, no key: `extract_json`, `check`, `text_matches`, `disagreements` (behaviors 9–17) |
| `week06/generate.py` | Image API through the SDK; writes images and `manifest.json` (behaviors 18–19) |
| `week06/critique.py` | Vision calls through the SDK; `--compare` (behaviors 17, 19) |
| `week06/tests/test_checklist.py` | No-key tests for the checker |
| `week06/tests/test_generate.py` | No-key tests for the manifest with a fake client, and the no-key exit |
| `week06/tests/conftest.py` | Puts `week06/` on the import path |
| `week06/images/` | Five FLUX images, `manifest.json`, `critique.json`, `critique-mimo.json` |
| `week06/images-seed/`, `week06/images-nb/` | The seed re-run and the comparison model's image |
| `week06/CHECKS.md` | Costs, verdicts, seed check, comparison, step-5 record, linter, Review |

### Order of work
1. **Checker.** Tests first (all met, unmet named, unanswered, invented, loose text, not JSON,
   JSON in prose, name mismatch, two critics). Red (no `checklist.py`). Write it. Green.
2. **Generator.** Tests first with a fake client (manifest fields, cost carried, `--only`, no-key
   exit). Red. Write `generate.py`. Green.
3. **Critic.** `critique.py` on top of `checklist.py`; tests for the no-key exit and `--compare`.
   Red, then green. `ruff check .`; record findings. Commit "Image set: checker with tests".
4. **Eval (billed, about $0.15).** Five generations, five critiques on MiniMax, the seed re-run of
   one prompt, the comparison model on one prompt. Look at every image before reading critiques.
   Commit "Image set: five images, critiques, two image models".
5. **The critic checked.** Critiques on MiMo, `--compare`, every disagreement checked by eye; the
   open-ended critique (run by Ethan in his own terminal); three sentences. Commit "Image set: the
   critic checked".

### Risks
- **The image model misspells a name** (likely: text is where image models fail most). That is a
  result, not a bug; the checker reports it and nothing is regenerated.
- **The critic misreads a correct name, or says "met" when it is not.** Code cannot see the image;
  the second model and a person looking are the only checks. Every disagreement is looked at.
- **MiMo returns empty or cut-off replies** if its reasoning is on. The per-model table sets
  `{"effort": "none"}`; `finish_reason` is recorded per call.
- **The comparison model rejects `seed`.** Recorded as the finding, not worked around.
- **Cost.** A model call inside a test, or the eval in a loop, multiplies the bill. No test calls
  a model; the eval is run by hand, once.
- **Blast radius:** local files in `week06/` and about $0.15.

### Proof
**Without a key** (`.venv/bin/python -m pytest week06/tests`, under a second, free): the checker on
hand-written critiques (behaviors 9–17), the manifest with a fake client (18), and the no-key exit
(19). These prove the code's judgments on known inputs; they do not prove any model reads an image
correctly.

**With the key** (by hand, once, about $0.15): five FLUX images ($0.07), five MiniMax and five MiMo
critiques with a name read each (under $0.02), one seed re-run ($0.014), one Gemini image
($0.03–0.04). This shows what the models actually did on these prompts; it proves nothing about
other prompts, and a person checks every disagreement.

### Questions asked before approval
1. **"If the critic says a requirement is unmet and it is actually met, which test notices?"**
   Answer: none. No test can, because no test looks at the image. The second model (`--compare`)
   and a person looking catch it. *Correction:* the first draft's Proof said the checker tests
   "catch wrong critiques"; it now says what they do not prove.
2. **"What does one run of the eval cost, and what happens if I run it in a loop by mistake?"**
   Answer: about $0.15; a loop multiplies it. *Correction:* added `--only NAME` to the generator so
   the seed check and the comparison model regenerate one prompt, not all five.
3. **"What does the same seed guarantee, and how would I check that?"** Answer: the same model,
   prompt, and seed should give the same picture, not necessarily the same file bytes. Check both:
   look at the two images, then `cmp` the files, and record both answers.

**Approved by:** Ethan Ambrossi, 2026-10-31
