"""Generate the creature image set through OpenRouter's Image API and write a manifest.

    python3 generate.py prompts.json --out images                       # needs OPENROUTER_API_KEY
    python3 generate.py prompts.json --out images-seed --only profowl   # the seed check
    python3 generate.py prompts.json --model google/gemini-3.1-flash-lite-image --out images-nb --only profowl

One billed call per prompt (FLUX.2 klein: about $0.014). The manifest records prompt, seed,
requirements, expected name, model, media type, file, cost from the reply, and seconds, so the
critic and the checker never guess what was asked for. Spec behaviors 18 and 19.
"""
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "black-forest-labs/flux.2-klein-4b"
EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def generate_one(client, model: str, prompt: str, seed: int, aspect_ratio: str) -> dict:
    """One Image API call (POST /api/v1/images through the SDK): bytes, media type, cost."""
    r = client.images.generate(model=model, prompt=prompt, aspect_ratio=aspect_ratio, seed=seed)
    item = r.data[0]
    return {"bytes": base64.b64decode(item.b64_json), "media_type": item.media_type,
            "cost": getattr(r.usage, "cost", None)}


def run(client, prompts: list[dict], out: Path, model: str, aspect_ratio: str,
        only: str | None = None) -> list[dict]:
    """Generate each prompt once (or only the named one), save the images, write manifest.json."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for p in prompts:
        if only and p["name"] != only:
            continue
        t0 = time.time()
        g = generate_one(client, model, p["prompt"], p["seed"], aspect_ratio)
        path = out / f"{p['name']}.{EXT.get(g['media_type'], 'bin')}"
        path.write_bytes(g["bytes"])
        entry = {**p, "model": model, "aspect_ratio": aspect_ratio, "file": path.name,
                 "media_type": g["media_type"], "cost": g["cost"], "seconds": round(time.time() - t0, 1)}
        manifest.append(entry)
        print(f"{path}  {g['media_type']}  seed={p['seed']}  ${g['cost']}  {entry['seconds']}s")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("prompts", type=Path)
    ap.add_argument("--out", type=Path, default=Path("images"))
    ap.add_argument("--model", default=os.environ.get("IMAGE_MODEL", DEFAULT_MODEL))
    ap.add_argument("--aspect-ratio", default="1:1")
    ap.add_argument("--only", help="generate just the prompt with this name")
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set; image generation is a billed call. Nothing generated.")
    from openrouter import OpenRouter  # imported here so the no-key path and the tests never need it

    manifest = run(OpenRouter(api_key=key), json.loads(args.prompts.read_text()), args.out,
                   args.model, args.aspect_ratio, args.only)
    total = sum(e["cost"] or 0.0 for e in manifest)
    print(f"{len(manifest)} image(s), ${total:.4f} total, manifest in {args.out / 'manifest.json'}")


if __name__ == "__main__":
    main()
