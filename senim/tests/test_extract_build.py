from senim.extract import build, find_dois, find_urls
from tests.conftest import EXTRACTION, SAMPLE


def test_build_locates_spans_and_links_citations():
    lang, claims, cits = build(SAMPLE, EXTRACTION)
    assert lang == "ru"
    assert [c.id for c in claims] == ["c1", "c2"]
    c1 = claims[0]
    assert SAMPLE[c1.start:c1.end] == c1.span == "Абай Кунанбаев родился в 1847 году"
    assert cits[0].doi == "10.5555/senim.fake.2021"
    assert cits[0].claim_ids == ["c1"]


def test_invented_span_is_not_trusted():
    data = {"language": "ru", "claims": [{"text": "Луна сделана из сыра.", "span": "Луна сделана из сыра", "type": "general"}],
            "citations": []}
    _, claims, _ = build(SAMPLE, data)
    assert claims[0].span is None and claims[0].start is None


def test_opinions_are_not_checkable_and_bad_types_fall_back():
    data = {"language": "ru", "claims": [
        {"text": "Абай — лучший поэт.", "type": "opinion", "checkable": True},
        {"text": "Абай умер в 1904 году.", "type": "weird-type"},
    ], "citations": []}
    _, claims, _ = build(SAMPLE, data)
    assert claims[0].checkable is False
    assert claims[1].type == "general" and claims[1].checkable


def test_safety_net_adds_missed_doi_and_url():
    text = "См. https://example.org/paper. Также doi:10.1234/ABC.5678)."
    _, _, cits = build(text + " " * 20, {"language": "en", "claims": [], "citations": []})
    assert {c.doi for c in cits if c.doi} == {"10.1234/abc.5678"}
    assert {c.url for c in cits if c.url} == {"https://example.org/paper"}


def test_regexes_strip_trailing_punctuation():
    assert find_dois("(doi:10.1038/s41586-024-07421-0).") == ["10.1038/s41586-024-07421-0"]
    assert find_urls("see https://adilet.zan.kz/rus/docs/K950001000_, and more") == ["https://adilet.zan.kz/rus/docs/K950001000_"]
    assert find_urls("https://doi.org/10.1/x") == []


def test_extractor_cannot_silently_correct_the_claim():
    data = {"language": "ru", "claims": [{
        "text": "Абай Кунанбаев родился в 1847 году.", "span": "Абай Кунанбаев родился в 1847 году",
        "type": "date", "answer": "1845"}], "citations": []}   # extractor "fixed" the year
    _, claims, _ = build(SAMPLE, data)
    assert claims[0].answer == "1847"


def test_faithful_answer_keeps_good_values():
    from senim.extract import faithful_answer
    assert faithful_answer("1847", "родился в 1847 году") == "1847"
    assert faithful_answer("Astana", "The capital is Astana") == "Astana"
    assert faithful_answer("25 желтоқсан 1991", "1991 жылы 25 желтоқсанда") == "25 желтоқсан 1991"
