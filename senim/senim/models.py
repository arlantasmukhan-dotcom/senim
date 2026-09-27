"""Data shapes shared by the pipeline, the sensors and the API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

ClaimType = Literal[
    "number", "date", "quote", "citation", "law", "name_fact",
    "causal", "general", "opinion", "advice", "prediction",
]
SensorStatus = Literal["ok", "off", "skipped", "error"]
Stance = Literal["supports", "contradicts", "irrelevant"]
Relation = Literal["agree", "contradict", "unsure"]
VerdictLabel = Literal["confirmed", "unconfirmed", "suspicious", "contradicted", "not_checkable"]

UNCHECKABLE_TYPES = {"opinion", "advice", "prediction"}


class Claim(BaseModel):
    id: str
    text: str
    span: Optional[str] = None          # verbatim piece of the original answer, used for highlighting
    start: Optional[int] = None
    end: Optional[int] = None
    type: ClaimType = "general"
    checkable: bool = True
    lang: str = "ru"
    entity: Optional[str] = None
    entity_kind: Optional[str] = None
    question: Optional[str] = None
    question_alt: Optional[str] = None
    answer: Optional[str] = None
    search_queries: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    id: str
    raw: str
    doi: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    claim_ids: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    url: str
    domain: str
    title: str = ""
    tier: int = 4
    stance: Stance = "irrelevant"
    quote: str = ""
    locked: bool = False                 # True only if the quote literally exists in the page text
    snippet_only: bool = False           # page text was only a search snippet, not the full page


class AlibiResult(BaseModel):
    status: SensorStatus = "ok"
    backend: str = ""                    # "tavily" or "wikipedia"
    queries: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    rejected_quotes: int = 0             # quote not found on the page (Quote-Lock)
    weak_quotes: int = 0                 # quote is real but does not contain the number/date at stake
    support_domains: list[str] = Field(default_factory=list)
    contradict_domains: list[str] = Field(default_factory=list)
    contradict_tier12: bool = False
    contradict_other: bool = False
    suggested_correction: Optional[str] = None
    note: str = ""


class WitnessAnswer(BaseModel):
    model: str
    phrasing: int
    answer: str
    relation: Relation = "unsure"


class ReinterrogationResult(BaseModel):
    status: SensorStatus = "ok"
    answers: list[WitnessAnswer] = Field(default_factory=list)
    agree_share: float = 0.0
    contradict_share: float = 0.0
    unsure_share: float = 0.0
    note: str = ""


class PhantomAnswer(BaseModel):
    answer: str
    fabricated: bool


class PhantomResult(BaseModel):
    status: SensorStatus = "ok"
    fake_entity: str = ""
    twin_question: str = ""
    nonexistence_verified: bool = False
    verified_by: str = ""                # "wikipedia" or "web" (Tavily exact-name search)
    target_model: str = ""
    answers: list[PhantomAnswer] = Field(default_factory=list)
    bluff: float = 0.0
    note: str = ""


class FameResult(BaseModel):
    status: SensorStatus = "ok"
    qid: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    sitelinks: dict[str, str] = Field(default_factory=dict)
    views: dict[str, int] = Field(default_factory=dict)
    total_views: int = 0
    bucket: Literal["famous", "known", "rare", "unknown"] = "unknown"
    tail_risk: float = 1.0
    note: str = ""


CitationVerdict = Literal[
    "fabricated", "frankenstein", "not_supporting", "unverifiable_text",
    "supports", "dead_link", "never_existed", "unchecked",
]


class CitationResult(BaseModel):
    citation_id: str
    raw: str
    verdict: CitationVerdict = "unchecked"
    exists: Optional[bool] = None
    found_title: Optional[str] = None
    found_year: Optional[int] = None
    found_authors: list[str] = Field(default_factory=list)
    mismatches: list[str] = Field(default_factory=list)
    support_quote: Optional[str] = None
    lookup: str = ""                     # which service answered: handle, crossref, openalex, http, wayback
    claim_ids: list[str] = Field(default_factory=list)
    note: str = ""                       # technical note (English, for developers)
    reason: str = ""                     # glass-box explanation in the UI language


class Verdict(BaseModel):
    claim_id: str
    label: VerdictLabel
    p_wrong: Optional[float] = None
    features: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    source_quote: Optional[str] = None
    source_url: Optional[str] = None
    suggested_correction: Optional[str] = None
    tip: str = ""


class CheckRequest(BaseModel):
    text: str
    question: Optional[str] = None
    author_model: Optional[str] = None   # OpenRouter id of the model that (most likely) wrote the answer
    ui_lang: Literal["ru", "kk", "en"] = "ru"
    mode: Literal["quick", "deep"] = "deep"
