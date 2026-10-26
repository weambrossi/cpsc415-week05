# Intent: receipts to data

## Goal
A command-line program that takes one photograph of a receipt, asks a vision model to read it into
JSON (merchant, date, items with quantity and unit price, subtotal, discount, tax, total), and then
checks in plain code that the items add up to the subtotal and that subtotal, discount and tax
produce the total. It reports any problem it finds; it never corrects the numbers.

## Who it is for
Me, as a student who wants to turn paper receipts (dining hall, bookstore, pharmacy) into data
without typing them in. Today I would retype each line by hand, or trust whatever a chatbot reads
off the photo, and a vision model returns numbers that look right whether or not they are.

## Constraints
- Python 3 in a virtual environment, the same setup as Weeks 3 and 4.
- Models through OpenRouter with the key from `OPENROUTER_API_KEY`: `minimax/minimax-m3` (the class
  model) and `xiaomi/mimo-v2.6-flash`, compared on the same five receipts. Each read costs well
  under a cent; the whole lab should stay under $0.10.
- One model call per image. The arithmetic check is ordinary code, never a second model call.
- Tests come before the code they test. Tests that need no key cover the checker and the JSON
  parsing; an eval that needs the key compares each image with `images/expected.json`.
- `images/` and `images/expected.json` are the answer key and are never edited.
- No API key in the repository.

## Not in scope
Fixing a receipt's numbers, a web or phone interface, storing receipts in a database, currency
conversion, and multi-page receipts. Reading card numbers or names is not wanted at all.

## Success looks like
- `python read_receipt.py images/receipt-01.png` prints the receipt as JSON, then "No problems
  found", and the merchant is Mather Dining Hall with a total of 13.66.
- A receipt whose numbers do not add up is reported with the expected and the printed amount, for
  example "items sum to 12.84 but subtotal is 12.48 (off by 0.36)".
- The eval runs all five course receipts on both models and prints, per receipt, what matched
  `expected.json` and the tokens in and out. The results are in `CHECKS.md`.

## Open questions
None left. Settled in the interview:
- **Discount sign.** Receipts print it as `-1.15` or `1.15`. The JSON holds discount as a
  non-negative amount taken off, so total = subtotal − discount + tax.
- **Missing year.** If the receipt does not print a year (receipt-05 says "Oct 3"), the date is
  null rather than a guessed year. A two-digit year (`10/04/26`) counts as printed.
- **No subtotal line.** The subtotal is null and the check compares the items directly with the
  total after discount and tax.

**Approved by:** Ethan Ambrossi, 2026-10-26
