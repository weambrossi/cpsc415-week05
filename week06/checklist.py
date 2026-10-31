"""The checker: plain code that judges a critique. No model, no key (spec.md behaviors 9-17).

The critic is a model and may be wrong. This code cannot see the image. What it can say for sure:
did the critic answer every requirement, answer only those, and say each was met; and does the
name it read back match the name the prompt asked for.
"""
import json
import re


def extract_json(text: str | None) -> dict | None:
    """The JSON object inside a reply (bare, in prose, or in a code fence), or None."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def check(requirements: list[str], critique: dict | None) -> dict:
    """Compare the critic's checklist with the requirements.

    Returns ok, a list of problems, and the requirements unmet, missing (not answered), and
    extra (answered but never asked). Anything other than met == True counts as unmet.
    """
    if critique is None or not isinstance(critique.get("checks"), list):
        return {"ok": False, "problems": ["critique was not the JSON checklist that was asked for"],
                "unmet": [], "missing": list(requirements), "extra": []}
    answered = {}
    for c in critique["checks"]:
        if isinstance(c, dict) and isinstance(c.get("requirement"), str):
            answered[_norm(c["requirement"])] = c
    wanted = {_norm(r): r for r in requirements}
    missing = [r for k, r in wanted.items() if k not in answered]
    extra = [c["requirement"] for k, c in answered.items() if k not in wanted]
    unmet = [r for k, r in wanted.items() if k in answered and answered[k].get("met") is not True]
    problems = []
    if missing:
        problems.append(f"critic did not answer {len(missing)} requirement(s)")
    if extra:
        problems.append(f"critic answered {len(extra)} item(s) that were not asked")
    if unmet:
        problems.append(f"{len(unmet)} requirement(s) reported unmet")
    return {"ok": not problems, "problems": problems, "unmet": unmet, "missing": missing, "extra": extra}


def text_matches(expected: str, read: str | None) -> bool:
    """The name read equals the name asked for, ignoring case, spaces, and punctuation."""
    if not read:
        return False
    return _norm(expected) == _norm(read)


def disagreements(a: list[dict], b: list[dict]) -> list[dict]:
    """Images where two critique files differ on any requirement or on the name read."""
    by_name = {e["name"]: e for e in b}
    out = []
    for ea in a:
        eb = by_name.get(ea["name"])
        if eb is None:
            continue
        va, vb = _verdicts(ea), _verdicts(eb)
        text = {**{k: v[0] for k, v in vb.items()}, **{k: v[0] for k, v in va.items()}}
        diffs = [{"requirement": text[k], "a": va.get(k, (None, None))[1], "b": vb.get(k, (None, None))[1]}
                 for k in sorted(text) if va.get(k, (None, None))[1] != vb.get(k, (None, None))[1]]
        if _norm(ea.get("text_read") or "") != _norm(eb.get("text_read") or ""):
            diffs.append({"requirement": "<name read>", "a": ea.get("text_read"), "b": eb.get("text_read")})
        if diffs:
            out.append({"name": ea["name"], "diffs": diffs})
    return out


def _verdicts(entry: dict) -> dict:
    """Normalized requirement -> (requirement as the critic wrote it, met)."""
    checks = (entry.get("critique") or {}).get("checks") or []
    return {_norm(c["requirement"]): (c["requirement"], c.get("met")) for c in checks
            if isinstance(c, dict) and isinstance(c.get("requirement"), str)}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
