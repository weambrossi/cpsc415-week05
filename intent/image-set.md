# Intent: creature image set

## Goal
A command-line program that turns five text prompts into five pictures of original pocket
creatures, each with its name printed in a banner at the top. A vision model then answers a yes/no
checklist about each picture, and plain code checks those answers: did the critic answer every
item, answer only those items, say each was met, and does the name it read match the name asked
for. It reports every problem it finds; it never fixes or regenerates an image.

## Who it is for
Fans who want to design their own creature-collector monsters from a sentence ("a professor owl").
Today they draw by hand or use a general image tool, which drifts from the style, adds extra
characters or stray text, and misspells names, and a chatbot asked "is this right?" answers with
confidence whether or not it is.

## Constraints
- Python 3 in the Week 5 `.venv`, in a new `week06/` folder of this repository.
- Image generation through the OpenRouter Image API with `black-forest-labs/flux.2-klein-4b`
  (about $0.014 per image), plus one comparison image model on one prompt.
- Critique through a vision model on the chat endpoint: `minimax/minimax-m3`, checked by a second
  model, `xiaomi/mimo-v2.6-flash`.
- One generation per prompt and one critique per image, each with a fixed seed. No automatic
  retries. The whole billed run should stay under $0.25.
- The creatures are original designs. Prompts describe a style ("cute creature-collector monster,
  anime game art") and never name an existing franchise, character, or real person.
- Tests come before the code they test. The checker is tested without a key on hand-written
  critiques; tests that call a model are skipped when no key is set and never loop over a model.
- No API key in the repository.

## The prompt family
Fixed in every prompt: one original creature, centered, full body, plain white background,
creature-collector game art, its name in a banner at the top. Varies: the concept.

| # | Concept | Name text | Its own requirements |
|---|---|---|---|
| 1 | Professor owl | PROFOWL | wears glasses; holds a book or pointer |
| 2 | Student fox | STUDEX | wears a backpack; holds a pencil |
| 3 | Robot | BOLTBIT | metal body with visible bolts or panels; glowing eyes |
| 4 | Chef frog | CHEFROG | wears a chef's hat; holds a spoon |
| 5 | Athlete turtle | DASHELL | wears a sweatband; is in a running pose |

Every image is also checked for: exactly one creature; a plain white background; the name in a
banner at the top; no text other than the name. Six yes/no items per image.

## Not in scope
A web interface (that is Team Project 1's job), regenerating or editing a failed image, choosing
the "best" of several images, user-uploaded photos, audio, and judging whether a creature looks
good. The program checks the critique; it does not know what is in the picture.

## Success looks like
- Five images in `week06/images/` with a `manifest.json` that records, for each, the prompt, seed,
  model, media type, and the cost from the reply.
- For each image the program prints either "ok" or each problem by name: a requirement unmet, a
  requirement the critic did not answer, a requirement the critic invented, a critique that was
  not JSON, or a name mismatch such as expected "PROFOWL", read "PROFOWI".
- Running the second vision model and comparing the two critique files lists every item where they
  disagree, and `CHECKS.md` records, for each, what I saw in the image.

## Open questions
None blocking. Seeds, file formats, and the exact checklist wording are settled in the spec.

**Approved by:** Ethan Ambrossi, 2026-10-31
