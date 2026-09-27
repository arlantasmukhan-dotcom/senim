from datetime import date

from senim.models import Citation, Claim, WitnessAnswer
from senim.sensors.alibi import apply_judgement
from senim.sensors.citations import compare_metadata, inverted_index_to_text
from senim.sensors.fame import bucket_for, last_12_months
from senim.sensors.reinterrogate import is_refusal, numeric_relation, summarize
from senim.sources import registrable_domain, tier_of

CLAIM = Claim(id="c1", text="Абай родился в 1847 году.", type="date", answer="1847")
PAGES = [
    {"url": "https://ru.wikipedia.org/wiki/Абай", "title": "Абай", "text": "Абай родился 10 августа 1845 года."},
    {"url": "https://kk.wikipedia.org/wiki/Абай", "title": "Абай", "text": "Абай 1845 жылы 10 тамызда туған."},
    {"url": "https://someblog.example/abai", "title": "blog", "text": "Абай появился на свет в 1847 году, пишут некоторые."},
]


def test_alibi_quote_lock_and_tiers():
    judgement = {"assessments": [
        {"source": "S1", "stance": "contradicts", "quote": "Абай родился 10 августа 1845 года"},
        {"source": "S2", "stance": "contradicts", "quote": "Абай 1845 жылы 10 тамызда туған"},
        {"source": "S3", "stance": "supports", "quote": "Абай появился на свет в 1847 году"},
        {"source": "S1", "stance": "supports", "quote": "совершенно выдуманная цитата из воздуха"},
        {"source": "S9", "stance": "supports", "quote": "unknown source id is ignored"},
    ], "suggested_correction": "Абай родился в 1845 году."}
    res = apply_judgement(CLAIM, PAGES, judgement)
    assert res.rejected_quotes == 1
    assert res.contradict_tier12 is True
    # ru. and kk.wikipedia are ONE independent source
    assert res.contradict_domains == ["wikipedia.org"]
    assert res.support_domains == ["someblog.example"]
    assert res.suggested_correction == "Абай родился в 1845 году."


def test_alibi_no_correction_without_locked_contradiction():
    judgement = {"assessments": [{"source": "S1", "stance": "contradicts", "quote": "invented text not on page"}],
                 "suggested_correction": "whatever"}
    res = apply_judgement(CLAIM, PAGES, judgement)
    assert not res.contradict_domains and res.suggested_correction is None


def test_source_tiers():
    assert tier_of("https://adilet.zan.kz/rus/docs/K950001000_") == 1
    assert tier_of("https://www.stat.gov.kz/ru/") == 1
    assert tier_of("https://kk.wikipedia.org/wiki/X") == 2
    assert tier_of("https://tengrinews.kz/x") == 3
    assert tier_of("https://otvet.mail.ru/question/1") == 4
    assert tier_of("https://random-site.xyz") == 4
    assert registrable_domain("https://www.bbc.co.uk/news") == "bbc.co.uk"


def test_numeric_relation_and_refusals():
    assert numeric_relation("1845", "Абай родился 10 августа 1845 года.") == "agree"
    assert numeric_relation("1845", "В 1847 году.") == "contradict"
    assert numeric_relation("1845", "Не знаю точно.") == "unsure"
    assert numeric_relation("Astana", "Astana") is None
    assert numeric_relation("1845", "в середине века") is None
    # same year, different day: must NOT count as agreement
    assert numeric_relation("1991 жылы 25 желтоқсан", "1991 жылы 16 желтоқсанда") == "contradict"
    assert numeric_relation("1991 жылы 25 желтоқсан", "25 желтоқсан 1991") == "agree"
    assert numeric_relation("1991 жылы 25 желтоқсан", "1991 жылы") is None
    for text in ["unknown", "I don't know", "Мәлімет жоқ", "Нет информации об этом человеке", "Такого поэта не существует"]:
        assert is_refusal(text), text
    assert not is_refusal("Он родился в 1932 году в Семее.")


def test_summarize_shares():
    answers = [WitnessAnswer(model="m", phrasing=1, answer="x", relation=r)
               for r in ["agree", "agree", "contradict", "unsure"]]
    res = summarize(answers)
    assert (res.agree_share, res.contradict_share, res.unsure_share) == (0.5, 0.25, 0.25)


def test_fame_buckets_and_dates():
    assert bucket_for(0, False) == "unknown"
    assert bucket_for(500, True) == "rare"
    assert bucket_for(50_000, True) == "known"
    assert bucket_for(2_000_000, True) == "famous"
    assert last_12_months(date(2026, 9, 26)) == ("20250901", "20260831")
    assert last_12_months(date(2026, 1, 5)) == ("20250101", "20251231")


def test_citation_metadata_comparison():
    cit = Citation(id="r1", raw="x", title="Detecting hallucinations in large language models using semantic entropy",
                   year=2024, authors=["Farquhar", "Kossen"])
    same = compare_metadata(cit, "Detecting hallucinations in large language models using semantic entropy", 2024,
                            ["Sebastian Farquhar", "Jannik Kossen"])
    assert same == []
    wrong = compare_metadata(cit, "A totally different paper about rivers", 2019, ["Ivanov"])
    assert set(wrong) == {"title", "year", "authors"}


def test_inverted_index():
    assert inverted_index_to_text({"world": [1], "hello": [0]}) == "hello world"


def test_unreachable_wikimedia_is_an_error_not_max_risk(monkeypatch):
    import asyncio
    from senim import net
    from senim.sensors import fame

    async def rate_limited(url, params=None, **kw):
        return 429, None
    monkeypatch.setattr(net, "get_json", rate_limited)
    res = asyncio.run(fame.run(Claim(id="c", text="x", entity="Abai Kunanbayev")))
    assert res.status == "error" and res.tail_risk == 0.5


def test_unreachable_wikipedia_makes_alibi_error(monkeypatch):
    import asyncio
    from senim import llm, net
    from senim.config import settings
    from senim.sensors import alibi

    async def rate_limited(url, params=None, **kw):
        return 429, None
    async def never_called(*a):
        raise AssertionError("judge must not run without sources")
    monkeypatch.setattr(net, "get_json", rate_limited)
    monkeypatch.setattr(settings, "tavily_api_key", "")
    llm.set_backend(never_called)
    try:
        res = asyncio.run(alibi.run(Claim(id="c", text="Абай родился в 1845 году.", lang="ru", search_queries=["Абай"])))
    finally:
        llm.set_backend(None)
    assert res.status == "error" and "search failed" in res.note


def test_rate_limited_pageviews_do_not_fake_a_rare_topic(monkeypatch):
    import asyncio
    from senim import net
    from senim.sensors import fame
    from tests.conftest import fake_get_json

    async def partial(url, params=None, **kw):
        if "pageviews" in url:
            return 429, None
        return await fake_get_json(url, params)
    monkeypatch.setattr(net, "get_json", partial)
    res = asyncio.run(fame.run(Claim(id="c", text="x", entity="Abai Kunanbayev")))
    assert res.status == "error"


def test_numeric_claims_need_the_number_in_the_quote():
    pages = [{"url": "https://e-history.kz/abai", "title": "Абай",
              "text": "Родился в Чингисских горах в семье старшины. Абай родился 10 августа 1845 года."}]
    judgement = {"assessments": [
        {"source": "S1", "stance": "contradicts", "quote": "Родился в Чингисских горах в семье старшины"},  # no year
    ]}
    res = apply_judgement(CLAIM, pages, judgement)
    assert res.weak_quotes == 1 and not res.contradict_domains and not res.contradict_tier12
    judgement = {"assessments": [{"source": "S1", "stance": "contradicts", "quote": "Абай родился 10 августа 1845 года"}]}
    res = apply_judgement(CLAIM, pages, judgement)
    assert res.contradict_domains == ["e-history.kz"] and res.contradict_tier12  # e-history.kz is tier 2


def test_support_domains_sorted_by_trust():
    pages = [
        {"url": "https://youtube.com/watch?v=1", "title": "v", "text": "Абай появился на свет в 1847 году точно"},
        {"url": "https://ru.wikipedia.org/wiki/A", "title": "w", "text": "Абай появился на свет в 1847 году точно"},
    ]
    judgement = {"assessments": [
        {"source": "S1", "stance": "supports", "quote": "Абай появился на свет в 1847 году"},
        {"source": "S2", "stance": "supports", "quote": "Абай появился на свет в 1847 году"},
    ]}
    assert apply_judgement(CLAIM, pages, judgement).support_domains == ["wikipedia.org", "youtube.com"]


def test_russian_plurals():
    from senim.explain import ru_plural
    assert [ru_plural(n, "раз", "раза", "раз") for n in (1, 2, 4, 5, 6, 11, 21, 22)] == \
        ["раз", "раза", "раза", "раз", "раз", "раз", "раз", "раза"]


def test_phantom_falls_back_to_web_search(monkeypatch):
    import asyncio
    from senim import net
    from senim.config import settings
    from senim.sensors import alibi, phantom

    async def blocked(url, params=None, **kw):
        return 403, None
    async def search(query, include_domains=None):
        return [{"url": "https://x.kz", "title": "Результаты", "text": "Ничего похожего тут нет"}]
    monkeypatch.setattr(net, "get_json", blocked)
    monkeypatch.setattr(alibi, "tavily_search", search)
    monkeypatch.setattr(settings, "tavily_api_key", "test")
    assert asyncio.run(phantom.exists_on_wikipedia("Ерлан Жаксыгалиев")) is None
    assert asyncio.run(phantom.exists_on_web("Ерлан Жаксыгалиев")) is False
    monkeypatch.setattr(settings, "tavily_api_key", "")
    assert asyncio.run(phantom.exists_on_web("Ерлан Жаксыгалиев")) is None


def test_centuries_are_not_compared_as_numbers():
    assert numeric_relation("9th century", "He was born around 870.") is None
    assert numeric_relation("IX век", "около 870 года") is None
    assert numeric_relation("XIX ғасыр", "1845 жылы") is None
