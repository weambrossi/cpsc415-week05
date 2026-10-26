"""Checks a parsed receipt's arithmetic in plain code. No model call (spec behaviors 6-9).

A receipt is the dictionary reader.parse_reply returns. check() reports problems; it never fixes them.
"""

TOLERANCE = 0.01  # dollars; one cent of rounding is allowed on each sum


def _mismatch(what, expected, printed):
    """A sentence naming both amounts and the difference, or None if they agree within a cent."""
    diff = round(abs(expected - printed), 2)
    if diff <= TOLERANCE:
        return None
    return f"{what} is {expected:.2f} but the receipt says {printed:.2f} (off by {diff:.2f})"


def check(receipt):
    """Return a list of problems with the receipt's numbers. An empty list means they add up."""
    items_sum = round(sum(i["quantity"] * i["unit_price"] for i in receipt["items"]), 2)
    problems = []

    subtotal = receipt.get("subtotal")
    if subtotal is None:
        subtotal = items_sum  # no subtotal line: compare the items with the total directly
    else:
        problem = _mismatch("items sum", items_sum, subtotal)
        if problem:
            problems.append(problem)

    expected_total = round(subtotal - receipt.get("discount", 0) + receipt.get("tax", 0), 2)
    problem = _mismatch("subtotal - discount + tax", expected_total, receipt["total"])
    if problem:
        problems.append(problem)
    return problems
