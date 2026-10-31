"""No-key tests for the generator and the CLI exits: spec.md behaviors 17-19.

The Image API is replaced by a fake client, so nothing here is billed.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from generate import run

HERE = Path(__file__).resolve().parents[1]
PROMPTS = [
    {"name": "profowl", "prompt": "an owl", "seed": 6101, "requirements": ["a"], "expected_text": "PROFOWL"},
    {"name": "studex", "prompt": "a fox", "seed": 6102, "requirements": ["b"], "expected_text": "STUDEX"},
]


class FakeImages:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        item = SimpleNamespace(b64_json=base64.b64encode(b"fake-jpeg").decode(), media_type="image/jpeg")
        return SimpleNamespace(data=[item], usage=SimpleNamespace(cost=0.014))


def fake_client():
    return SimpleNamespace(images=FakeImages())


def test_18_manifest_has_one_entry_per_prompt_with_every_field(tmp_path):
    client = fake_client()
    manifest = run(client, PROMPTS, tmp_path, "black-forest-labs/flux.2-klein-4b", "1:1")
    assert [e["name"] for e in manifest] == ["profowl", "studex"]
    for entry in manifest:
        for field in ("prompt", "seed", "requirements", "expected_text", "model", "aspect_ratio",
                      "file", "media_type", "cost", "seconds"):
            assert field in entry
        assert entry["cost"] == 0.014
        assert entry["media_type"] == "image/jpeg"
        assert (tmp_path / entry["file"]).read_bytes() == b"fake-jpeg"
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest


def test_18_seed_and_prompt_are_sent_as_given(tmp_path):
    client = fake_client()
    run(client, PROMPTS, tmp_path, "m", "1:1")
    assert [(c["seed"], c["prompt"], c["model"]) for c in client.images.calls] == [
        (6101, "an owl", "m"), (6102, "a fox", "m")]


def test_18_only_generates_one_prompt(tmp_path):
    client = fake_client()
    manifest = run(client, PROMPTS, tmp_path, "m", "1:1", only="studex")
    assert len(client.images.calls) == 1
    assert [e["name"] for e in manifest] == ["studex"]


def _no_key_env():
    env = dict(os.environ)
    env.pop("OPENROUTER_API_KEY", None)
    return env


def test_19_no_key_no_call():
    for script in (["generate.py", "prompts.json"], ["critique.py", "images/manifest.json"]):
        r = subprocess.run([sys.executable, *script], cwd=HERE, env=_no_key_env(),
                           capture_output=True, text=True, check=False)
        assert r.returncode == 1
        assert "OPENROUTER_API_KEY is not set" in r.stderr


def test_17_compare_needs_no_key_and_lists_disagreements(tmp_path):
    a = [{"name": "profowl", "critique": {"checks": [{"requirement": "Wears glasses", "met": True}]},
          "text_read": "PROFOWL"}]
    b = [{"name": "profowl", "critique": {"checks": [{"requirement": "Wears glasses", "met": False}]},
          "text_read": "PROFOWL"}]
    (tmp_path / "a.json").write_text(json.dumps(a))
    (tmp_path / "b.json").write_text(json.dumps(b))
    r = subprocess.run([sys.executable, "critique.py", "--compare", str(tmp_path / "a.json"),
                        str(tmp_path / "b.json")], cwd=HERE, env=_no_key_env(), capture_output=True, text=True, check=False)
    assert r.returncode == 0
    assert "Wears glasses: True vs False" in r.stdout
    assert "1 image(s) where the two critics disagree" in r.stdout
