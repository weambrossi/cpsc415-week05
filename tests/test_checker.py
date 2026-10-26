"""Checker tests: plain arithmetic on hand-written receipts. No key needed (spec behaviors 6-9)."""

from checker import check


def item(name, quantity, unit_price):
    return {"name": name, "quantity": quantity, "unit_price": unit_price}


def receipt(items, subtotal, total, discount=0, tax=0):
    return {"merchant": "Test", "date": None, "items": items, "subtotal": subtotal,
            "discount": discount, "tax": tax, "total": total}


# receipt-01's numbers
DINING = [item("Chicken wrap", 1, 7.49), item("Side salad", 1, 3.25), item("Iced tea", 1, 2.10)]


def test_receipt_that_adds_up_has_no_problems():
    assert check(receipt(DINING, 12.84, 13.66, tax=0.82)) == []


def test_wrong_subtotal_is_reported_with_both_amounts_and_difference():
    problems = check(receipt(DINING, 12.48, 13.30, tax=0.82))
    assert len(problems) == 1
    assert "12.84" in problems[0] and "12.48" in problems[0] and "0.36" in problems[0]


def test_wrong_total_is_reported_with_both_amounts_and_difference():
    # The lab's step-4 number: 13.96 printed where 13.66 is right.
    problems = check(receipt(DINING, 12.84, 13.96, tax=0.82))
    assert len(problems) == 1
    assert "13.66" in problems[0] and "13.96" in problems[0] and "0.30" in problems[0]


def test_discount_is_subtracted():
    # receipt-03: 11.50 - 1.15 + 0.66 = 11.01
    coffee = [item("Latte 12oz", 1, 4.75), item("Croissant", 1, 3.50), item("Americano", 1, 3.25)]
    assert check(receipt(coffee, 11.50, 11.01, discount=1.15, tax=0.66)) == []


def test_discount_added_instead_of_subtracted_is_caught():
    coffee = [item("Latte 12oz", 1, 4.75), item("Croissant", 1, 3.50), item("Americano", 1, 3.25)]
    problems = check(receipt(coffee, 11.50, 13.31, discount=1.15, tax=0.66))
    assert len(problems) == 1 and "2.30" in problems[0]


def test_quantities_multiply_unit_price():
    # receipt-02: 2 x 1.25 and 3 x 0.89 among six lines
    books = [item("Blue book", 2, 1.25), item("Notebook 80pg", 1, 4.99), item("Gel pen", 3, 0.89),
             item("Hoodie navy L", 1, 44.00), item("USB-C cable 1m", 1, 12.99), item("Highlighter", 1, 1.49)]
    assert check(receipt(books, 68.64, 73.00, tax=4.36)) == []


def test_missing_subtotal_uses_items_sum_for_the_total():
    # receipt-05: no subtotal line, no tax
    bake = [item("Brownie", 1, 2.00), item("Cookies", 3, 1.00), item("Lemonade", 1, 1.50)]
    assert check(receipt(bake, None, 6.50)) == []
    problems = check(receipt(bake, None, 7.50))
    assert len(problems) == 1 and "6.50" in problems[0] and "7.50" in problems[0]


def test_one_cent_rounding_is_tolerated():
    assert check(receipt([item("A", 3, 0.333)], 1.00, 1.00)) == []
