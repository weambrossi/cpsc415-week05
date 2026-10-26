"""Reads a receipt image into a dictionary with a vision model (spec component 1).

parse_reply turns a model's reply into a receipt or raises ReadError; it needs no key.
read_receipt sends the image to OpenRouter and parses the reply.

Environment (loaded from .env if present):
    OPENROUTER_API_KEY  your OpenRouter key (never put it in a file in this repo)
    CHAT_MODEL          vision model, default minimax/minimax-m3
    CHAT_REASONING      on | off, overrides the per-model REASONING table
"""

import base64
import json
import mimetypes
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 60
MAX_TOKENS = 4000
CHAT_MODEL = os.environ.get("CHAT_MODEL", "minimax/minimax-m3")

# Reasoning is a per-model decision (spec, Model): MiniMax reads the faded date only with it on;
# MiMo spends its whole budget thinking and returns nothing unless it is off.
REASONING = {"minimax/minimax-m3": True, "xiaomi/mimo-v2.6-flash": False}

PROMPT = """Read this receipt. Reply with one JSON object and nothing else, in this shape:
{"merchant": string, "date": "YYYY-MM-DD" or null, "items": [{"name": string, "quantity": number,
"unit_price": number}], "subtotal": number or null, "discount": number, "tax": number, "total": number}

Rules:
- merchant: the store name as printed at the top, not the address or a slogan.
- date: only if the receipt prints a year (a two-digit year like 26 means 2026). If no year is
  printed, date is null. Do not guess a year.
- items: one entry per item line. "3 x Gel pen" is one item with quantity 3; unit_price is the
  price of one (the "@ ... ea" price, or the line amount divided by the quantity).
- subtotal: the printed subtotal, or null if there is no subtotal line.
- discount: the amount taken off, as a positive number; 0 if none.
- tax: 0 if none. total: the printed total.
- Copy the printed numbers. Do not correct them even if they do not add up.
- Ignore card numbers and names."""


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


def reasoning_for(model):
    """Whether to leave the model's reasoning on: CHAT_REASONING wins, then the table, then on."""
    setting = os.environ.get("CHAT_REASONING", "").lower()
    if setting in ("on", "off"):
        return setting == "on"
    return REASONING.get(model, True)


def read_receipt(path, model=None):
    """Send one image to the model and parse the reply. Returns (receipt, usage). Raises ReadError."""
    model = model or os.environ.get("CHAT_MODEL", CHAT_MODEL)
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or ""
    if not path.is_file() or not mime.startswith("image/"):
        raise ReadError(f"{path} is not an image file")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ReadError("OPENROUTER_API_KEY is not set. Put it in .env (gitignored) or export it.")

    image = base64.b64encode(path.read_bytes()).decode()
    body = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image}"}},
        ]}],
    }
    if not reasoning_for(model):
        body["reasoning"] = {"enabled": False}

    try:
        response = requests.post(URL, json=body, timeout=TIMEOUT,
                                 headers={"Authorization": f"Bearer {key}"})
    except requests.RequestException as e:
        raise ReadError(f"could not reach OpenRouter: {e}")
    if response.status_code != 200:
        raise ReadError(f"HTTP {response.status_code} from OpenRouter: {response.text[:300]}")
    data = response.json()
    if "error" in data:
        raise ReadError(str(data["error"].get("message", data["error"])))
    choice = data["choices"][0]
    reply = choice["message"].get("content") or ""
    if not reply.strip():
        raise ReadError(f"empty reply from {model} (finish_reason: {choice.get('finish_reason')})")
    return parse_reply(reply), data.get("usage", {})
