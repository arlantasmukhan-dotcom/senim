"""Text helpers: normalization, Quote-Lock, span location, passage selection."""

from __future__ import annotations

import difflib
import json
import re
import unicodedata

_QUOTES = str.maketrans({
    "«": '"', "»": '"', "„": '"', "“": '"', "”": '"', "‟": '"', "″": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'", "`": "'",
    "–": "-", "—": "-", "―": "-", "‐": "-", "‑": "-", "−": "-",
    " ": " ", " ": " ", " ": " ", " ": " ",
})
_INVISIBLE = re.compile(r"[­​‌‍⁠﻿]")
_SPACES = re.compile(r"\s+")
_WORD = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    """Lower-case, unify quotes/dashes/spaces, drop invisible characters.

    Only formatting is normalized, never wording: Quote-Lock must stay strict.
    """
    text = unicodedata.normalize("NFC", text or "")
    text = _INVISIBLE.sub("", text).translate(_QUOTES)
    text = text.replace("ё", "е").replace("Ё", "Е")
    return _SPACES.sub(" ", text).strip().casefold()


def quote_lock(quote: str, page_text: str, min_len: int = 12) -> bool:
    """True only if `quote` literally occurs in `page_text` (after formatting normalization).

    This is the guard that stops the LLM judge from inventing evidence: a quote that
    is not on the page is thrown away, whatever the judge said about it.
    """
    q = normalize(quote).strip(" .\"'")
    if len(q) < min_len:
        return False
    return q in normalize(page_text)


def locate_span(span: str | None, text: str) -> tuple[int, int] | None:
    """Find `span` inside the original `text`; returns (start, end) in original indices."""
    if not span:
        return None
    idx = text.find(span)
    if idx >= 0:
        return idx, idx + len(span)
    # Formatting-tolerant search: walk the original text and compare normalized windows.
    target = normalize(span)
    if not target:
        return None
    sentences = split_sentences_with_offsets(text)
    for start, end in sentences:
        if target in normalize(text[start:end]):
            return start, end
    # Last resort: best fuzzy sentence match.
    best, best_ratio = None, 0.0
    for start, end in sentences:
        ratio = difflib.SequenceMatcher(None, target, normalize(text[start:end])).ratio()
        if ratio > best_ratio:
            best, best_ratio = (start, end), ratio
    return best if best_ratio >= 0.6 else None


_SENT_END = re.compile(r"(?<=[.!?…])\s+|\n+")


def split_sentences_with_offsets(text: str) -> list[tuple[int, int]]:
    spans, pos = [], 0
    for m in _SENT_END.finditer(text):
        if m.start() > pos:
            spans.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        spans.append((pos, len(text)))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def words(text: str) -> list[str]:
    return [w for w in _WORD.findall(normalize(text)) if len(w) > 2 or w.isdigit()]


def best_passages(page_text: str, query: str, max_chars: int = 2400, window: int = 600) -> str:
    """Pick the parts of a long page that overlap most with the claim (cheap BM25-like scoring)."""
    page_text = page_text or ""
    if len(page_text) <= max_chars:
        return page_text
    q = set(words(query))
    if not q:
        return page_text[:max_chars]
    chunks = [page_text[i:i + window] for i in range(0, len(page_text), window // 2)]
    scored = []
    for i, chunk in enumerate(chunks):
        w = words(chunk)
        if not w:
            continue
        hits = sum(1 for t in w if t in q)
        digits = sum(1 for t in q if t.isdigit() and t in w)  # numbers matter most for facts
        scored.append((hits + 3 * digits, i))
    scored.sort(reverse=True)
    picked, total = [], 0
    for _, i in scored:
        if total + len(chunks[i]) > max_chars:
            break
        picked.append(i)
        total += len(chunks[i])
    return "\n…\n".join(chunks[i] for i in sorted(picked))


_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUM.findall(text or "")}


def parse_json_block(text: str):
    """Parse the first JSON object/array in an LLM reply (tolerates ```json fences and chatter)."""
    if text is None:
        raise ValueError("empty reply")
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON found in reply")


def title_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    na = " ".join(words(a))
    nb = " ".join(words(b))
    return difflib.SequenceMatcher(None, na, nb).ratio()
