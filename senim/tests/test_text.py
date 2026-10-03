from senim.text import best_passages, locate_span, normalize, parse_json_block, quantities, quote_lock, same_number


def test_quote_lock_accepts_formatting_differences():
    page = "Абай Кунанбаев (10 августа 1845 года — 6 июля 1904 года) — казахский поэт."
    assert quote_lock("абай кунанбаев (10 августа 1845 года - 6 июля 1904 года)", page)
    assert quote_lock("«Абай Кунанбаев (10 августа 1845 года — 6 июля 1904 года)»", page)


def test_quote_lock_rejects_paraphrase_and_invention():
    page = "Абай Кунанбаев родился 10 августа 1845 года в Чингизских горах."
    assert not quote_lock("Абай родился в 1845 году в горах Чингиз", page)
    assert not quote_lock("Абай Кунанбаев родился 10 августа 1847 года", page)


def test_quote_lock_rejects_too_short_quotes():
    assert not quote_lock("1845", "born in 1845")
    assert not quote_lock("", "anything at all here")


def test_normalize_handles_yo_and_invisible_chars():
    assert normalize("Ёлка­  «тест»") == 'елка "тест"'


def test_locate_span_exact_and_tolerant():
    text = "Первое предложение. Абай умер в 1904 году. Конец."
    assert text[slice(*locate_span("Абай умер", text))] == "Абай умер"
    start, end = locate_span("абай умер в 1904 году", text)
    assert "1904" in text[start:end]
    assert locate_span("совсем другое утверждение про космос", text) is None
    assert locate_span(None, text) is None


def test_parse_json_block_variants():
    assert parse_json_block('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_block('Sure! Here it is: {"a": [1, 2]} hope it helps') == {"a": [1, 2]}
    assert parse_json_block("[1, 2]") == [1, 2]


def _values(text):
    return [n.value for n in quantities(text)]


def test_numbers_by_value():
    assert _values("10 августа 1845 года, 3,5 км") == [10, 1845, 3.5]
    assert _values("20,000") == _values("20 000") == _values("20 000") == [20000]
    assert _values("2,700,000 и 2.700.000") == [2_700_000, 2_700_000]
    assert _values("2,7 млн") == _values("2.7 million") == [2_700_000]
    assert _values("3 мың") == [3000] and _values("1,5 млрд") == [1.5e9]
    assert _values("10.08.1845") == [10, 8, 1845]
    assert _values("10 км") == [10]  # "к" of "км" is not the "k" (thousand) scale


def test_rounded_numbers_match():
    two_point_seven = quantities("2,7 млн")[0]
    assert same_number(two_point_seven, quantities("2 700 000 человек")[0])
    assert same_number(two_point_seven, quantities("2 683 000")[0])      # "2,7 млн" is a rounded figure
    assert not same_number(two_point_seven, quantities("3 100 000")[0])
    assert not same_number(quantities("1845")[0], quantities("1847")[0])


def test_best_passages_keeps_relevant_part():
    filler = "Нерелевантный текст про погоду. " * 300
    page = filler + "Абай Кунанбаев родился в 1845 году." + filler
    out = best_passages(page, "Абай Кунанбаев родился 1845", max_chars=1500)
    assert "1845" in out and len(out) <= 1600
