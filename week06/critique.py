"""Critique the image set with a vision model, then check the critique in code.

    python3 critique.py images/manifest.json                                   # MiniMax M3, needs the key
    python3 critique.py images/manifest.json --model xiaomi/mimo-v2.6-flash --out images/critique-mimo.json
    python3 critique.py --compare images/critique.json images/critique-mimo.json   # no key

Per image: one call with the yes/no checklist (JSON reply), one narrow call asking for the name
exactly as printed. The judging is plain code in checklist.py; the critique is never trusted.
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

from checklist import check, disagreements, extract_json, text_matches

DEFAULT_MODEL = "minimax/minimax-m3"
# Hidden reasoning is per model (Week 5 setup, section 2). MiMo needs it off; through the SDK
# that is {"effort": "none"} ({"enabled": False} is silently sent as {}). MiniMax keeps it on.
REASONING = {"xiaomi/mimo-v2.6-flash": {"effort": "none"}}

CHECKLIST_PROMPT = """You are checking a generated image against the prompt that produced it.
Prompt: {prompt}

Answer every item below with true or false, strictly from what is visible in the image.
Reply with one JSON object and nothing else:
{{"checks": [{{"requirement": "<item text, copied exactly>", "met": true, "evidence": "<one short sentence>"}}, ...]}}

Items:
{items}"""

NAME_PROMPT = ("Write the largest piece of text in this image exactly as printed, character for "
               "character. Reply with that text only.")


def ask(client, model: str, image: Path, media_type: str, question: str, max_tokens: int) -> tuple[str | None, dict]:
    """One vision call through the chat endpoint: the question plus the image as a data URL."""
    data = base64.b64encode(image.read_bytes()).decode()
    kwargs = {"reasoning": REASONING[model]} if model in REASONING else {}
    c = client.chat.send(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{data}"}}]}], **kwargs)
    usage = {"in": c.usage.prompt_tokens, "out": c.usage.completion_tokens,
             "cost": getattr(c.usage, "cost", None)} if c.usage else {}
    usage["finish"] = c.choices[0].finish_reason      # "length" means the budget ran out mid-answer
    return c.choices[0].message.content, usage


def critique_set(client, model: str, manifest_path: Path) -> list[dict]:
    results = []
    for entry in json.loads(manifest_path.read_text()):
        image = manifest_path.parent / entry["file"]
        items = "\n".join(f"- {r}" for r in entry["requirements"])
        raw, usage = ask(client, model, image, entry["media_type"],
                         CHECKLIST_PROMPT.format(prompt=entry["prompt"], items=items), 1500)
        critique = extract_json(raw)
        result = {"name": entry["name"], "model": model, "critique": critique, "raw": raw, "usage": usage,
                  "check": check(entry["requirements"], critique)}
        read, usage2 = ask(client, model, image, entry["media_type"], NAME_PROMPT, 400)
        result["text_read"] = (read or "").strip()
        result["text_matches"] = text_matches(entry["expected_text"], read)
        result["usage_text"] = usage2
        results.append(result)
        c = result["check"]
        verdict = "ok" if c["ok"] else "; ".join(
            c["problems"] + [f"unmet: {u}" for u in c["unmet"]] + [f"missing: {m}" for m in c["missing"]]
            + [f"invented: {x}" for x in c["extra"]])
        match = "match" if result["text_matches"] else f"MISMATCH (expected {entry['expected_text']!r})"
        print(f"{entry['name']}: {verdict}  | name read {result['text_read']!r} {match}"
              f"  [{usage.get('in')} in / {usage.get('out')} out, {usage.get('finish')}]")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifest", nargs="?", type=Path)
    ap.add_argument("--model", default=os.environ.get("CHAT_MODEL", DEFAULT_MODEL))
    ap.add_argument("--out", type=Path, help="default: critique.json beside the manifest")
    ap.add_argument("--compare", nargs=2, type=Path, metavar=("A.json", "B.json"))
    args = ap.parse_args()

    if args.compare:
        a, b = (json.loads(p.read_text()) for p in args.compare)
        diffs = disagreements(a, b)
        for d in diffs:
            print(d["name"])
            for x in d["diffs"]:
                print(f"  {x['requirement']}: {x['a']!r} vs {x['b']!r}")
        print(f"{len(diffs)} image(s) where the two critics disagree. Look at those yourself.")
        return
    if args.manifest is None:
        ap.error("manifest.json is required (or use --compare)")
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; the critique is a billed vision call per image. Nothing checked.")
    from openrouter import OpenRouter

    results = critique_set(OpenRouter(api_key=key), args.model, args.manifest)
    out = args.out or args.manifest.parent / "critique.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    bad = [r["name"] for r in results if not r["check"]["ok"] or not r["text_matches"]]
    print(f"{len(results) - len(bad)}/{len(results)} images pass the code's check; written to {out}")


if __name__ == "__main__":
    main()
