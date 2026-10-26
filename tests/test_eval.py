"""The eval: each image read by the model and compared with the folder's expected.json.

Needs OPENROUTER_API_KEY; skipped without it. RECEIPT_DIR picks the folder (default images/),
CHAT_MODEL the model. Each image is read once (see the reads fixture in conftest.py).
"""

import pytest
from conftest import expected

from checker import check

EXPECTED = expected()
NAMES = sorted(EXPECTED)

pytestmark = pytest.mark.model


@pytest.mark.parametrize("name", NAMES)
def test_merchant(reads, name):
    assert reads(name)["merchant"].lower() == EXPECTED[name]["merchant"].lower()


@pytest.mark.parametrize("name", NAMES)
def test_date(reads, name):
    assert reads(name)["date"] == EXPECTED[name]["date"]


@pytest.mark.parametrize("name", NAMES)
def test_item_count(reads, name):
    assert len(reads(name)["items"]) == EXPECTED[name]["items"]


@pytest.mark.parametrize("name", NAMES)
def test_total(reads, name):
    assert reads(name)["total"] == pytest.approx(EXPECTED[name]["total"], abs=0.01)


@pytest.mark.parametrize("name", NAMES)
def test_checker_finds_no_problems(reads, name):
    assert check(reads(name)) == []
