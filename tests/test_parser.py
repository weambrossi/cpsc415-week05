"""Parser tests: model replies written by hand. No key needed (spec behaviors 1-5, 10)."""

import json

import pytest

from reader import ReadError, parse_reply

GOOD = {
    "merchant": "Mather Dining Hall",
    "date": "2026-10-02",
    "items": [{"name": "Chicken wrap", "quantity": 1, "unit_price": 7.49},
              {"name": "Side salad", "quantity": 1, "unit_price": 3.25},
              {"name": "Iced tea", "quantity": 1, "unit_price": 2.10}],
    "subtotal": 12.84,
    "discount": 0,
    "tax": 0.82,
    "total": 13.66,
}


def test_plain_json():
    assert parse_reply(json.dumps(GOOD)) == GOOD


def test_json_inside_prose():
    reply = f"Here is the receipt you asked for:\n{json.dumps(GOOD)}\nLet me know if you need more."
    assert parse_reply(reply) == GOOD


def test_json_inside_code_fence():
    reply = f"```json\n{json.dumps(GOOD, indent=2)}\n```"
    assert parse_reply(reply) == GOOD


def test_reply_that_is_not_json_is_a_failed_read():
    with pytest.raises(ReadError, match="not JSON"):
        parse_reply("Sorry, I can't read this image clearly.")


def test_broken_json_is_a_failed_read_not_a_crash():
    with pytest.raises(ReadError):
        parse_reply('{"merchant": "Mather", "total": 13.66,')


@pytest.mark.parametrize("field", ["merchant", "items", "total"])
def test_missing_required_field_is_named(field):
    reply = {k: v for k, v in GOOD.items() if k != field}
    with pytest.raises(ReadError, match=field):
        parse_reply(json.dumps(reply))


def test_string_numbers_and_dollar_signs_become_numbers():
    reply = dict(GOOD, total="$13.66", tax="0.82",
                 items=[{"name": "Chicken wrap", "quantity": "1", "unit_price": "$7.49"}])
    r = parse_reply(json.dumps(reply))
    assert r["total"] == 13.66 and r["tax"] == 0.82
    assert r["items"][0]["quantity"] == 1 and r["items"][0]["unit_price"] == 7.49


def test_missing_discount_and_tax_become_zero():
    reply = {k: v for k, v in GOOD.items() if k not in ("discount", "tax")}
    r = parse_reply(json.dumps(reply))
    assert r["discount"] == 0 and r["tax"] == 0


def test_null_discount_and_tax_become_zero():
    r = parse_reply(json.dumps(dict(GOOD, discount=None, tax=None)))
    assert r["discount"] == 0 and r["tax"] == 0


def test_negative_discount_is_stored_as_amount_taken_off():
    r = parse_reply(json.dumps(dict(GOOD, discount=-1.15)))
    assert r["discount"] == 1.15


def test_missing_subtotal_stays_null():
    r = parse_reply(json.dumps(dict(GOOD, subtotal=None)))
    assert r["subtotal"] is None


def test_missing_quantity_defaults_to_one():
    r = parse_reply(json.dumps(dict(GOOD, items=[{"name": "Brownie", "unit_price": 2.0}])))
    assert r["items"][0]["quantity"] == 1


@pytest.mark.parametrize("date", ["Oct 3", "10/03", "2026-10", "", None])
def test_date_that_is_not_iso_becomes_null(date):
    assert parse_reply(json.dumps(dict(GOOD, date=date)))["date"] is None


def test_non_number_total_is_a_failed_read():
    with pytest.raises(ReadError, match="total"):
        parse_reply(json.dumps(dict(GOOD, total="about thirteen")))
