# Week 6 checks: creature image set

All runs on October 31, 2026. Image model `black-forest-labs/flux.2-klein-4b`; critic
`minimax/minimax-m3` (reasoning on), checked by `xiaomi/mimo-v2.6-flash` (reasoning off,
`{"effort": "none"}`). Costs are `usage.cost` from each reply. **Total for the lab: $0.126.**

## The test loop: red, then green
| Step | Red | Green |
|---|---|---|
| Checker (`test_checklist.py`, 11 tests) | `ModuleNotFoundError: checklist` | 10/11 first; `test_17_two_critics_disagree` failed because the report printed the normalized requirement text instead of the critic's wording. Fixed in `_verdicts`, then 11/11. |
| Generator and CLI (`test_generate.py`, 5 tests) | `ModuleNotFoundError: generate` | 16/16 in 0.12 s, no key. |

Setup finding: the Week 5 `.venv/bin/pip` still pointed at the folder's old path
(`Desktop/CPSC-415/...`), so `pip install openrouter` silently did nothing and the tests still
passed (the SDK is imported only after the key check). Installed with `.venv/bin/python -m pip`.

## Per image (FLUX.2 klein, seeds 6101–6105, critic MiniMax M3)
| Image | Image cost | Seconds | Checker verdict | Name read | Match | Critique cost |
|---|---|---|---|---|---|---|
| profowl | $0.014 | 5.0 | ok (6/6 met) | PROFOWL | yes | $0.00143 |
| studex | $0.014 | 2.8 | ok (6/6 met) | STUDEX | yes | $0.00106 |
| boltbit | $0.014 | 3.5 | ok (6/6 met) | BOLTBIT | yes | $0.00115 |
| chefrog | $0.014 | 3.7 | ok (6/6 met) | CHEFROG | yes | $0.00132 |
| dashell | $0.014 | 3.6 | ok (6/6 met) | DASHELL | yes | $0.00100 |

Five images $0.070; five MiniMax critiques (checklist + name read) $0.0060. I looked at every
image before reading the critiques: all five names are spelled correctly and every requirement is
visibly met, with two borderline calls on DASHELL (a tied bandana rather than a sweatband, and a
mid-stride pose that reads as running only loosely).

## Seed check
`generate.py prompts.json --out images-seed --only profowl` (seed 6101 again, $0.014, 3.5 s).
- **Looking:** the same picture: same owl, glasses, book, banner, and pose. I could not find a
  difference by eye.
- **Bytes:** `cmp images/profowl.jpg images-seed/profowl.jpg` → differ at byte 23; 304,269 vs
  306,349 bytes.

So for FLUX.2 klein, the same seed means the same image, not the same file. Comparing by hash
would call these different; comparing by looking (or by the name read) calls them the same.

## Comparison image model
`--model google/gemini-3.1-flash-lite-image --out images-nb --only profowl` (seed 6101 accepted).
**Cost $0.0336** (2.4× FLUX), 3.2 s. Name spelled correctly; glasses and book present. It added a
graduation cap, robe, bow tie, and a satchel, and the book cover reads "ARCANE KNOWLEDGE", which
breaks "There is no text other than the name". MiniMax caught it: the checker reported
`unmet: There is no text other than the name`, with the evidence "The open book also contains
visible text including 'ARCANE KNOWLEDGE.'" (critique $0.00135). FLUX followed the "no other
text" instruction on all five; Gemini did not on its one.

## Step 5: the critic checked

### Second model and `--compare`
`critique.py images/manifest.json --model xiaomi/mimo-v2.6-flash --out images/critique-mimo.json`
(five critiques, $0.0015, every reply `finish: stop`), then
`critique.py --compare images/critique.json images/critique-mimo.json`:

```
0 image(s) where the two critics disagree. Look at those yourself.
```

No disagreements: both models said all 30 requirements were met and read all five names
correctly. That agrees with what I saw, but the evidence lines show where agreement hides a soft
call. On DASHELL's "The creature wears a sweatband", MiniMax said "a blue sweatband tied around its
head", while MiMo called it "a blue headband tied around its forehead" and still answered `true`.
The verdicts match, so `--compare` stays silent; only a person reading the evidence notices that
one model's own description does not say "sweatband".

### Open-ended critique
_Run by Ethan in his own terminal, not through the agent (lab step 5.2)._ Prompt: "Critique this
poster. What is wrong with it?" on `images/dashell.jpg`.

- Model:
- What it claimed:
- Which claims were true (compared with the checklist verdicts, the name read, and my eyes):

### Which check caught what
The narrow questions compared in code caught the one real failure in this run (Gemini's
"ARCANE KNOWLEDGE" text) and confirmed all five names letter by letter, which a glance can skip.
The second model caught nothing here, because both critics agreed; it can catch a critic that
says "met" wrongly only when the two models are wrong in different ways. A person looking was the
only check that noticed the sweatband/headband softness on DASHELL, so for Team Project 1's
critique path I would keep the narrow checklist and name read in code, show each item's evidence
line in the app, and add the second model only on items a person flags.

## Linter (`ruff check .`, ruff 0.17)
- `week06/generate.py`: I001, import formatting on the lazy `from openrouter import OpenRouter`. Fixed.
- `week06/tests/test_generate.py`: PLW1510 twice, `subprocess.run` without `check`. Fixed with
  `check=False` (the tests assert the return code themselves).
- `.claude/hooks/guard.py`: PIE810, `startswith` called twice. The course's guard file; left as
  installed here (fixed in the team repository, where the gate runs ruff on every push).

## Guard
`.claude/hooks/guard.py` and `.claude/settings.json` are still installed. Finding from step 0:
`pip install openrouter` passed the guard *before* the Week 6 spec named it, because the guard
checks for the package name anywhere in `spec.md` and the Week 5 spec already contained
`OPENROUTER_API_KEY`. A substring match is not a dependency list.

## Review
- **PR:** https://github.com/weambrossi/cpsc415-tp1-creatures/pull/2 (branch `week06-ethan`: the
  generator, `images/ethan/`, `prompts/ethan.json`). Built on the plan PR,
  https://github.com/weambrossi/cpsc415-tp1-creatures/pull/1, which was reviewed the same way.
- **Reviewer:** `review.py --base plan-ethan`. `minimax/minimax-m3` exited 2 on every attempt (it
  spent its 2,000-token budget reasoning and never answered; the gate fails closed), so the runs
  used `--model xiaomi/mimo-v2.6-flash`, about $0.002 each. Every run's output is a PR comment.
- **Findings by pass, run 1 (exit 1):**
  - Pass 1: manifest `requirements` spread from the prompt rather than the four shared ones.
  - Pass 2: no-key message goes to stderr, not stdout; a missing `usage.cost` was summed as $0.
  - Pass 3: `BLOCKED` lists more words than spec G4 named.
  - Pass 4: README pointed at another repository with no link.
- **Run 2 (exit 1):** pass 2: `r.data[0]` with no check for an empty reply; a failure mid-run lost
  the manifest. Pass 3: no-key message wording; one test asserting two things.
- **Run 3 (exit 1):** pass 2: an item whose own text says "no change needed". Pass 3: `IMAGE_MODEL`
  undocumented; an import inside tests. Pass 4: link not pinned to a commit.
- **Fixed** (tests first where code changed, committed red, then green): missing cost recorded as
  `null` and reported in the summary; empty reply raises a clear `RuntimeError`; `manifest.json`
  rewritten after every image so a failure keeps the record of images already paid for; spec G4,
  G5, G7 and failure handling made exact; `IMAGE_MODEL` documented; test split; import moved; link
  pinned. Tests went from 17 to 21.
- **Pushed back on:** run 1's pass-1 item was half right: the spec, not the code, was wrong
  (Ethan's prompts carry per-creature requirements on purpose), so the spec was fixed, not the
  code. Run 1's stderr item: an error message belongs on stderr; the spec now says so. Run 3's
  pass-2 item: a non-finding, answered on the PR. On PR 1, a finding that `test_repo.py` would fail
  on case (it lowercases both sides) and on Flask/Playwright (not in `requirements.txt` yet; failing
  then is the point), answered on the PR.
- **Exit code of the last run:** 0 ("No findings."), on both PRs.
- **Gate:** the pre-push hook ran ruff and the no-key tests before every push; all passed. On the
  first push it caught a ruff error (PIE810) in the course's own `guard.py`.
- **Approved by:** _(Joud, on GitHub, before the merge)_
