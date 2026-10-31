# Spec

## Intent
Implements [`intent/receipts.md`](intent/receipts.md).

## Components

### 1. Reader (`reader.py`)
- **What it does:** Sends one receipt image to a vision model as a base64 data URL next to a text
  prompt, asks for JSON only, and parses the reply into a receipt dictionary. Parsing is separate
  from the call (`parse_reply(text)`) so it can be tested without a key.
- **Language:** Python 3.13. **Why:** Weeks 3 and 4 were Python, the eval and tests are short
  scripts, and pytest's skip markers make "tests that need a key" one decorator. Java with
  JUnit 5 and Jackson was the alternative: stronger typing for the receipt record, but a Gradle
  build and more ceremony for a five-image lab.
- **Model:** `minimax/minimax-m3`, reasoning on (the default). **Why:** it is the class model and
  reads the date on the faded receipt only with reasoning on (setup page, about 150–200 thinking
  tokens). Compared against `xiaomi/mimo-v2.6-flash` with reasoning **off**, because with reasoning
  on it spends its whole budget thinking and returns empty content. Reasoning is a per-model
  setting: a table in `reader.py`, overridden by `CHAT_REASONING=on|off`. Neither is a frontier
  model; the lab compares two cheap vision models and the results go in `CHECKS.md`.
- **Interfaces:**
  - `read_receipt(path, model=CHAT_MODEL) -> (receipt, usage)`; raises `ReadError` on a failed read.
  - `parse_reply(text) -> receipt`; raises `ReadError`.
  - CLI: `python read_receipt.py IMAGE` prints the receipt JSON, then the checker's findings.
    Exit 0 when the read worked (problems or not), 1 on a failed read.
  - Receipt shape:
    `{"merchant": str, "date": "YYYY-MM-DD" | null, "items": [{"name": str, "quantity": number,
    "unit_price": number}], "subtotal": number | null, "discount": number, "tax": number,
    "total": number}`
- **Dependencies:** `requests`, `python-dotenv` (see Dependencies below).

### 2. Checker (`checker.py`)
- **What it does:** Plain code, no model. Takes a parsed receipt and returns a list of problems,
  each a sentence naming the expected amount, the printed amount, and the difference.
- **Language:** Python 3.13, same reason as the reader; it is a pure function.
- **Model:** none. **Why:** the point of the checker is that it does not trust a model. Asking a
  second model to check the first would add cost and a second source of plausible wrong numbers.
- **Interfaces:** `check(receipt) -> list[str]`; an empty list means the numbers add up.
- **Dependencies:** none.

### 3. Eval (`eval.py`) and tests (`tests/`)
- **What it does:** `eval.py` reads every image in a folder once, compares each with the folder's
  `expected.json` (merchant, date, item count, total, and that the checker found no problems), and
  prints PASS/FAIL per field plus tokens in and out. The pytest eval (`tests/test_eval.py`) does the
  same comparison as one test per receipt and field.
- **Interfaces:** `python eval.py [--dir images] [--model SLUG]`. `RECEIPT_DIR` and `CHAT_MODEL`
  are the environment equivalents.

## Behavior
Numbered requirements the tests check. "No key" means the test runs without `OPENROUTER_API_KEY`.

1. A reply that is not JSON is a failed read (`ReadError` with the first 200 characters of the
   reply), not a crash. *(no key)*
2. A reply with JSON inside prose or a Markdown code fence is parsed from the outermost `{...}`.
   *(no key)*
3. A reply missing a required field (`merchant`, `items`, `total`) is a failed read naming the
   field. *(no key)*
4. Numbers written as strings (`"7.49"`, `"$7.49"`) are converted to numbers; a missing `discount`
   or `tax` becomes 0. *(no key)*
5. A negative discount is stored as its absolute value: discount is the amount taken off.
   *(no key)*
6. The checker compares the sum of quantity × unit_price over the items with the subtotal, and
   reports a mismatch larger than $0.01 with both amounts and the difference. *(no key)*
7. The checker compares subtotal − discount + tax with the total and reports a mismatch larger than
   $0.01 the same way. *(no key)*
8. When the subtotal is null (no subtotal line), the checker uses the items' sum in its place for
   the total check. *(no key)*
9. A receipt whose numbers add up gets an empty problem list. *(no key)*
10. The date is an ISO date or null. The prompt tells the model to return null when the year is
    not printed, and `parse_reply` turns a date that is not `YYYY-MM-DD` into null. *(no key for
    the parse rule; the eval checks receipt-05 is null.)*
11. Item count is the number of item lines, not the sum of quantities ("2 x Blue book" is one
    item). *(eval)*
12. The eval calls the model once per image, never once per field. *(eval; the pytest eval caches
    reads in a module-scoped fixture.)*
13. Tests that call a model are marked `@pytest.mark.model` and are skipped when no key is set.

## Failure handling
- **Missing key:** `read_receipt` raises `ReadError("OPENROUTER_API_KEY is not set ...")`; the
  model tests are skipped, the others run.
- **HTTP error, timeout (60 s) or empty content:** `ReadError` with the status or
  `finish_reason`, so an empty reply caused by reasoning is visible as `finish_reason: length`.
- **Non-JSON or incomplete reply:** behaviors 1–3.
- **Hallucinated numbers:** caught only if they break the arithmetic (behaviors 6–8). A misread that
  still adds up (a wrong merchant name) is caught only by the eval against `expected.json`.
- **Image not found or not an image:** `ReadError` before any call is made.

## Cost estimate
One call per image: about 700–1,000 tokens in (image plus prompt) and 200–800 out (JSON plus
reasoning on MiniMax). At these models' prices that is well under $0.001 per receipt. Both models
on seven receipts, a few times over, is a few cents; a semester of reading a receipt a day is
under a dollar.

## Dependencies
| Package | Reason |
|---|---|
| `requests` | The HTTP call to OpenRouter, as in Weeks 3 and 4. By hand it would be `urllib.request` with manual JSON and error handling. |
| `python-dotenv` | Loads `OPENROUTER_API_KEY` and `CHAT_MODEL` from the gitignored `.env`. By hand, a few lines that parse `KEY=value`. |
| `pytest` | The test runner: assertions with readable diffs, fixtures for the cached eval reads, and skip markers for tests that need a key. By hand, a script of asserts with no skip or selection. |
| `ruff` | The linter the lab asks for (`ruff check .`). Development only. |
| `openrouter` | Week 6. The official OpenRouter SDK: `client.images.generate` calls the Image API (`POST /api/v1/images`) and `client.chat.send` sends the image to a vision model, one client for both request shapes. By hand it would be two `requests` calls with different bodies, base64 handling, and error handling. Its `reasoning` object has no `enabled` field, so MiMo needs `{"effort": "none"}`. |

## Out of scope
Correcting a receipt, any interface besides the command line, storage, currency conversion,
multi-page receipts, and reading card numbers or names. A second model as checker was ruled out
above.

## Week 6: image set

Implements [`intent/image-set.md`](intent/image-set.md). Everything lives in `week06/`. The
Week 5 receipt reader above is unchanged.

### 4. Generator (`week06/generate.py`)
- **What it does:** reads `prompts.json` (five prompts, each with a name, a seed, its
  requirements, and the expected name text), makes one Image API call per prompt, saves each image,
  and writes `manifest.json` beside the images.
- **Language:** Python 3.13, the same `.venv` as Weeks 3 to 5. **Why:** the class examples and the
  SDK are Python, and the checker below must share the manifest format. Java was considered; it has
  no OpenRouter SDK, so both HTTP requests would be written by hand for no gain in a lab this size.
- **Model:** `black-forest-labs/flux.2-klein-4b` (default). **Why:** the class image model, about
  $0.014 per image, accepts `seed` and `aspect_ratio`, 3 to 4 seconds per image. **Compared with**
  `google/gemini-3.1-flash-lite-image` on one prompt (PROFOWL, same seed): about $0.03 to $0.04 per
  image, priced per image token, and its output carries a SynthID watermark. The comparison records
  cost from `usage.cost` and whether the same requirements are met.
- **Interfaces:** `python3 generate.py prompts.json --out images [--model SLUG] [--only NAME]`.
  Each manifest entry: `name`, `prompt`, `seed`, `requirements`, `expected_text`, `model`,
  `aspect_ratio`, `file`, `media_type`, `cost`, `seconds`. `--only` regenerates one prompt (the
  seed check and the comparison model) without paying for all five.
- **Dependencies:** `openrouter` (see Dependencies).

### 5. Critic-checker (`week06/critique.py`, `week06/checklist.py`)
- **What it does:** for each image in a manifest, sends the image and a yes/no checklist made from
  that prompt's requirements to a vision model, asks for JSON, then a second, narrow question:
  "write the largest text in this image exactly as printed". `checklist.py` is plain code with no
  model and no key: it extracts the JSON, compares the checklist with the requirements, compares
  the name read with the expected name, and compares two critique files.
- **Language:** Python 3.13. **Why:** same as the generator; the checker is pure functions that
  the no-key tests import directly.
- **Model:** `minimax/minimax-m3` with reasoning on (the class vision model; 24/25 on the Week 5
  receipts). **Checked by:** `xiaomi/mimo-v2.6-flash` with reasoning off
  (`reasoning={"effort": "none"}`), the cheaper, faster model from Week 5. A second model is the
  check on the first; neither is trusted alone, and every disagreement is looked at by a person.
- **Interfaces:** `python3 critique.py images/manifest.json [--model SLUG] [--out FILE]` writes a
  critique file (per image: name, model, parsed critique, raw reply, usage, the code's check, the
  name read, whether it matched). `python3 critique.py --compare A.json B.json` needs no key and
  prints every requirement or name read where the two disagree.

### Behavior (Week 6)
Numbered requirements the tests check. "No key" means the test runs without `OPENROUTER_API_KEY`.

9. **All met (no key).** A critique that answers every requirement, and only those, with
   `met: true` is ok, with no problems.
10. **Unmet, named (no key).** A requirement answered `met: false` (or anything other than `true`)
    is reported unmet by its text.
11. **Unanswered requirement (no key).** A requirement missing from the critique is a problem, even
    if every answered one is met.
12. **Invented requirement (no key).** An item in the critique that was not asked is a problem and
    is reported by its text.
13. **Loose matching of requirement text (no key).** Case, spacing, and punctuation differences in
    the requirement text the critic copied back do not count as missing or invented.
14. **Not JSON is a failed critique, not a crash (no key).** A reply with no JSON object (or JSON
    without a `checks` list) fails the check with every requirement counted unanswered.
15. **JSON inside prose or code fences is extracted (no key).**
16. **Name text compared in code, not by the critic (no key).** The name read is compared with
    `expected_text` ignoring case, spaces, and punctuation; `PROFOWL` vs `PROF0WL` or `PROFOWI` is
    a mismatch; no reply is a mismatch.
17. **Two critics compared (no key).** `--compare` lists each image and each requirement (or the
    name read) where two critique files disagree, and nothing when they agree.
18. **Manifest (no key).** The generator writes one entry per prompt with the fields above,
    carrying the cost from the reply, tested with a fake client.
19. **No key, no call.** Without `OPENROUTER_API_KEY`, `generate.py` and `critique.py` print one
    line saying so and exit 1; nothing is billed.
20. **Eval (key).** Five images on FLUX.2 klein, five critiques on each vision model, with fixed
    seeds. Run by hand once; recorded in `CHECKS.md`. No test calls a model in a loop.

### Failure handling (Week 6)
- **Critique not JSON, or cut off** (`finish_reason` "length"): recorded as a failed critique with
  the raw reply kept, never retried automatically.
- **Image misspells the name:** reported as a name mismatch. The image is never regenerated.
- **Critic misreads a correct name** (the October 19 "Integratlon" case): the code cannot tell
  this apart from a real misspelling; the second model and a person looking at the image can.
- **Image model rejects `seed` or `aspect_ratio`:** the error is printed and that prompt is
  skipped; the finding (no reproducibility on that model) goes in `CHECKS.md`.

### Cost estimate (Week 6)
Five FLUX images at about $0.014 = $0.07; one Gemini comparison image about $0.035; one seed
re-run $0.014; ten critiques (two calls each) well under $0.02. About $0.15 for the lab. Running
the eval in a loop by mistake would multiply that, which is why no test calls a model.
