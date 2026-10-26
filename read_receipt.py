"""Read one receipt image and check its arithmetic.

Usage: python read_receipt.py IMAGE [--model SLUG]
Prints the receipt as JSON, then the checker's findings. Exit 0 if the read worked, 1 if it failed.
"""

import argparse
import json
import sys

from checker import check
from reader import ReadError, read_receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image")
    parser.add_argument("--model", help="OpenRouter model slug (default: CHAT_MODEL or minimax/minimax-m3)")
    args = parser.parse_args()
    try:
        receipt, usage = read_receipt(args.image, args.model)
    except ReadError as e:
        print(f"Failed read: {e}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    problems = check(receipt)
    if problems:
        print("\nProblems found:")
        for p in problems:
            print(f"- {p}")
    else:
        print("\nNo problems found.")
    print(f"\nTokens: {usage.get('prompt_tokens', '?')} in, {usage.get('completion_tokens', '?')} out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
