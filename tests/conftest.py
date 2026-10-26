"""Shared pytest setup: skip model tests without a key, and read each image once per run."""

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
RECEIPT_DIR = ROOT / os.environ.get("RECEIPT_DIR", "images")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    skip = pytest.mark.skip(reason="OPENROUTER_API_KEY is not set")
    for item in items:
        if "model" in item.keywords:
            item.add_marker(skip)


def expected():
    path = RECEIPT_DIR / "expected.json"
    return json.loads(path.read_text()) if path.exists() else {}


@pytest.fixture(scope="module")
def reads():
    """One model call per image, shared by every test in the module (spec behavior 12)."""
    from reader import ReadError, read_receipt

    cache = {}

    def get(name):
        if name not in cache:
            try:
                cache[name] = read_receipt(RECEIPT_DIR / name)[0]
            except ReadError as e:
                cache[name] = e
        if isinstance(cache[name], ReadError):
            pytest.fail(f"{name}: failed read: {cache[name]}")
        return cache[name]

    return get
