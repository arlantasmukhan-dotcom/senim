from senim.text import best_passages, locate_span, normalize, numbers, parse_json_block, quote_lock


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


def test_numbers():
    assert numbers("10 августа 1845 года, 3,5 км") == {"10", "1845", "3.5"}


def test_best_passages_keeps_relevant_part():
    filler = "Нерелевантный текст про погоду. " * 300
    page = filler + "Абай Кунанбаев родился в 1845 году." + filler
    out = best_passages(page, "Абай Кунанбаев родился 1845", max_chars=1500)
    assert "1845" in out and len(out) <= 1600
