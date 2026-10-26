# Checks

Real output from the runs on 2026-10-26. Each step's tests were committed before its code (see
`git log`: every "Step N tests" commit comes before the "Step N" code commit).

## The test loop: red, then green

| Step | Red run (tests before code) | Green run (after code) |
|---|---|---|
| 2. Checker | `ModuleNotFoundError: No module named 'checker'` · 1 error | `8 passed in 0.02s` |
| 3. Parser | `ModuleNotFoundError: No module named 'reader'` · 1 error | `28 passed in 0.03s` (8 checker + 20 parser) |
| 4. Model call | No key: `28 passed, 25 skipped`. With key: `ImportError: cannot import name 'read_receipt' from 'reader'` · `25 errors` | MiniMax: `1 failed, 24 passed in 13.24s` (receipt-05 merchant, below) |

Full suite with the key: `1 failed, 52 passed in 10.10s`. Without a key: `28 passed, 25 skipped`.

## Two models on the five course receipts

`python eval.py`, then the same command with only `CHAT_MODEL` changed. Each image is read once.

### `minimax/minimax-m3`, reasoning on

| Receipt | merchant | date | items | total | checker | Tokens in | Tokens out | Seconds |
|---|---|---|---|---|---|---|---|---|
| receipt-01.png | PASS | PASS | PASS | PASS | PASS | 953 | 237 | 2.6 |
| receipt-02.png | PASS | PASS | PASS | PASS | PASS | 953 | 440 | 2.6 |
| receipt-03.png | PASS | PASS | PASS | PASS | PASS | 953 | 277 | 1.5 |
| receipt-04.png | PASS | PASS | PASS | PASS | PASS | 1000 | 328 | 2.5 |
| receipt-05.png | FAIL | PASS | PASS | PASS | PASS | 953 | 253 | 2.2 |

24/25 checks passed. Tokens: 4,812 in, 1,535 out.

### `xiaomi/mimo-v2.6-flash`, reasoning off

| Receipt | merchant | date | items | total | checker | Tokens in | Tokens out | Seconds |
|---|---|---|---|---|---|---|---|---|
| receipt-01.png | PASS | PASS | PASS | PASS | PASS | 656 | 139 | 1.5 |
| receipt-02.png | PASS | PASS | PASS | PASS | PASS | 656 | 216 | 0.9 |
| receipt-03.png | PASS | PASS | PASS | PASS | PASS | 656 | 143 | 0.8 |
| receipt-04.png | PASS | PASS | PASS | PASS | PASS | 722 | 214 | 0.9 |
| receipt-05.png | FAIL | PASS | PASS | PASS | PASS | 656 | 119 | 0.9 |

24/25 checks passed. Tokens: 3,346 in, 831 out.

### The one failure, on both models: spec ambiguity, not a misread

`receipt-05.png merchant: got 'Bake Sale - CS Club', expected 'CS Club Bake Sale'`

The receipt prints "Bake Sale - CS Club". Both models copied it exactly, as the prompt asks
("the store name as printed"). The answer key reorders the words. The model is right about what is
on the paper and the key is a normalized name. The spec never said which one counts as the
merchant. I left the key and the test alone (the key is not ours to edit, and loosening the
comparison to word sets just for this receipt would be a test that passes for the wrong reason).

### What differed
- Same accuracy on these five clean receipts. Both got the faded, tilted receipt-04 and the
  null date on receipt-05.
- MiMo with reasoning off used about 30% fewer input tokens (the same image costs 656 vs 953) and
  about half the output tokens, and answered in about 1 s instead of 2–3 s. MiniMax's extra output
  is its reasoning.
- The discount on receipt-03 (printed `-1.15`) passed on both. The prompt asks for a positive
  amount and `parse_reply` takes the absolute value either way (spec behavior 5), so a sign
  mix-up cannot reach the checker.

## Linter (`ruff check .`, ruff 0.17.2)

```
PIE810 Call `startswith` once with a `tuple`
  --> .claude/hooks/guard.py:28:12
I001 [*] Import block is un-sorted or un-formatted
  --> tests/test_eval.py:7:1
Found 2 errors.
```

- I001 was in our test file: fixed with `ruff check --fix` (the `conftest` import grouped as
  third-party).
- PIE810 is in the course's `guard.py`, copied unchanged from `examples/guardrail-hook/`. Left as
  is: it is style only, and the copy should match the course's.

After the fix: `Found 1 error.` (PIE810 only).

## Step 4: breaking the loop on purpose

*To be filled in when the step is run.*

## Own receipts (`my-receipts/`)

*To be filled in after the photographs are added.*
