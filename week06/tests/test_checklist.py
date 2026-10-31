"""No-key tests for the checker: spec.md behaviors 9-17. No model, no key, under a second."""
from checklist import check, disagreements, extract_json, text_matches

REQS = ["Exactly one creature", "The creature wears glasses", "No text other than the name"]


def critique(*met, reqs=REQS):
    return {"checks": [{"requirement": r, "met": m, "evidence": "x"} for r, m in zip(reqs, met)]}


def test_9_all_met_is_ok():
    assert check(REQS, critique(True, True, True)) == {
        "ok": True, "problems": [], "unmet": [], "missing": [], "extra": []}


def test_10_unmet_requirement_is_named():
    result = check(REQS, critique(True, False, True))
    assert not result["ok"]
    assert result["unmet"] == ["The creature wears glasses"]


def test_10_anything_but_true_counts_as_unmet():
    c = critique(True, "yes", None)
    assert check(REQS, c)["unmet"] == ["The creature wears glasses", "No text other than the name"]


def test_11_unanswered_requirement_is_a_problem_even_if_the_rest_pass():
    result = check(REQS, critique(True, True, reqs=REQS[:2]))
    assert not result["ok"]
    assert result["missing"] == ["No text other than the name"]
    assert result["unmet"] == []


def test_12_invented_requirement_is_a_problem():
    c = critique(True, True, True)
    c["checks"].append({"requirement": "The colors are vibrant", "met": True})
    result = check(REQS, c)
    assert not result["ok"]
    assert result["extra"] == ["The colors are vibrant"]


def test_13_requirement_text_is_matched_loosely():
    c = critique(True, True, True, reqs=["exactly one creature.", "The creature wears GLASSES",
                                          "  no text other than the name "])
    assert check(REQS, c)["ok"]


def test_14_not_json_is_a_failed_critique_not_a_crash():
    for reply in ["Sorry, I can't see an image.", "", None, '{"verdict": "looks great"}', "[1, 2]"]:
        result = check(REQS, extract_json(reply))
        assert not result["ok"]
        assert result["missing"] == REQS


def test_15_json_inside_prose_and_fences_is_extracted():
    reply = 'Here is my answer:\n```json\n{"checks": [{"requirement": "a", "met": true}]}\n```\nHope it helps.'
    assert extract_json(reply) == {"checks": [{"requirement": "a", "met": True}]}


def test_16_name_text_is_compared_in_code():
    assert text_matches("PROFOWL", "Profowl")
    assert text_matches("PROFOWL", '  "PROFOWL!" ')
    assert not text_matches("PROFOWL", "PROFOWI")
    assert not text_matches("PROFOWL", "PROF0WL")
    assert not text_matches("PROFOWL", "PROFOWL THE WISE")
    assert not text_matches("PROFOWL", None)
    assert not text_matches("PROFOWL", "")


def test_17_two_critics_disagree():
    a = [{"name": "profowl", "critique": critique(True, True, True), "text_read": "PROFOWL"}]
    b = [{"name": "profowl", "critique": critique(True, False, True), "text_read": "PROFOWI"}]
    d = disagreements(a, b)
    assert [x["name"] for x in d] == ["profowl"]
    assert {x["requirement"] for x in d[0]["diffs"]} == {"The creature wears glasses", "<name read>"}


def test_17_two_critics_agree():
    a = [{"name": "profowl", "critique": critique(True, True, True), "text_read": "PROFOWL"}]
    assert disagreements(a, a) == []
