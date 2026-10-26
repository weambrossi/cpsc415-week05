"""Reads a receipt image into a dictionary with a vision model (spec component 1).

parse_reply turns a model's reply into a receipt or raises ReadError; it needs no key.
"""

import json
import re


class ReadError(Exception):
    """A failed read: no key, an HTTP error, an empty reply, or a reply that is not a usable receipt."""


REQUIRED = ("merchant", "items", "total")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _number(value, field):
    """A number from a number or a string like "$7.49". Raises ReadError otherwise."""
    if isinstance(value, bool):
        raise ReadError(f"{field} is not a number: {value!r}")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value.replace("$", "").replace(",", "").strip())
        except ValueError:
            pass
    raise ReadError(f"{field} is not a number: {value!r}")


def _extract_json(text):
    """The outermost {...} in the reply, so prose and code fences around it are ignored."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ReadError(f"reply is not JSON: {text[:200]!r}")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ReadError(f"reply is not JSON ({e.msg}): {text[:200]!r}")


def parse_reply(text):
    """Turn a model reply into a receipt dictionary (spec behaviors 1-5 and 10)."""
    data = _extract_json(text or "")
    if not isinstance(data, dict):
        raise ReadError(f"reply is not a JSON object: {text[:200]!r}")
    for field in REQUIRED:
        if data.get(field) is None:
            raise ReadError(f"reply is missing {field}")
    if not isinstance(data["items"], list):
        raise ReadError("items is not a list")

    items = []
    for n, raw in enumerate(data["items"], 1):
        if not isinstance(raw, dict) or raw.get("unit_price") is None:
            raise ReadError(f"item {n} has no unit_price: {raw!r}")
        quantity = raw.get("quantity")
        items.append({
            "name": str(raw.get("name", "")),
            "quantity": 1 if quantity is None else _number(quantity, f"item {n} quantity"),
            "unit_price": _number(raw["unit_price"], f"item {n} unit_price"),
        })

    date = data.get("date")
    subtotal = data.get("subtotal")
    return {
        "merchant": str(data["merchant"]).strip(),
        "date": date if isinstance(date, str) and ISO_DATE.match(date) else None,
        "items": items,
        "subtotal": None if subtotal is None else _number(subtotal, "subtotal"),
        "discount": abs(_number(data.get("discount") or 0, "discount")),
        "tax": _number(data.get("tax") or 0, "tax"),
        "total": _number(data["total"], "total"),
    }
