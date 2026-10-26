"""Run every image in a folder through the reader once and compare with the folder's expected.json.

Usage: python eval.py [--dir images] [--model SLUG]
Environment: RECEIPT_DIR and CHAT_MODEL are the defaults for --dir and --model; OPENROUTER_API_KEY is required.
Prints one Markdown table row per receipt (PASS/FAIL per field, tokens in and out), then any failure details.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from checker import check
from reader import CHAT_MODEL, ReadError, read_receipt, reasoning_for

FIELDS = ("merchant", "date", "items", "total", "checker")


def compare(receipt, want):
    """Field -> (passed, detail) for one receipt."""
    problems = check(receipt)
    got = {
        "merchant": (receipt["merchant"].lower() == want["merchant"].lower(), receipt["merchant"]),
        "date": (receipt["date"] == want["date"], receipt["date"]),
        "items": (len(receipt["items"]) == want["items"], len(receipt["items"])),
        "total": (abs(receipt["total"] - want["total"]) <= 0.01, receipt["total"]),
        "checker": (not problems, "; ".join(problems) or "no problems"),
    }
    return got


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=os.environ.get("RECEIPT_DIR", "images"))
    parser.add_argument("--model", default=os.environ.get("CHAT_MODEL", CHAT_MODEL))
    args = parser.parse_args()

    folder = Path(args.dir)
    expected = json.loads((folder / "expected.json").read_text())
    reasoning = "on" if reasoning_for(args.model) else "off"
    print(f"Model: {args.model} (reasoning {reasoning}), folder: {folder}/\n")
    print("| Receipt | " + " | ".join(FIELDS) + " | Tokens in | Tokens out | Seconds |")
    print("|---" * (len(FIELDS) + 4) + "|")

    details, passed, tokens_in, tokens_out = [], 0, 0, 0
    for name in sorted(expected):
        start = time.time()
        try:
            receipt, usage = read_receipt(folder / name, args.model)
        except ReadError as e:
            print(f"| {name} | " + " | ".join(["READ FAILED"] * len(FIELDS)) + " | - | - | - |")
            details.append(f"{name}: failed read: {e}")
            continue
        seconds = time.time() - start
        result = compare(receipt, expected[name])
        cells = ["PASS" if ok else "FAIL" for ok, _ in result.values()]
        n_in, n_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        tokens_in, tokens_out = tokens_in + n_in, tokens_out + n_out
        print(f"| {name} | " + " | ".join(cells) + f" | {n_in} | {n_out} | {seconds:.1f} |")
        for field, (ok, got) in result.items():
            if ok:
                passed += 1
            else:
                want = expected[name].get(field, "no problems")
                details.append(f"{name} {field}: got {got!r}, expected {want!r}")

    total = len(expected) * len(FIELDS)
    print(f"\n{passed}/{total} checks passed. Tokens: {tokens_in} in, {tokens_out} out.")
    for line in details:
        print(f"- {line}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
