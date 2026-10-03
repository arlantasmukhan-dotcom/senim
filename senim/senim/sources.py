"""Source registry: how much a domain is trusted (tier 1 = official/primary, tier 4 = unknown/forums).

Tiers only weight evidence; a tier-4 page can still support a claim, it just counts for less.
Extend the lists as the team finds good sources.
"""

from __future__ import annotations

from urllib.parse import urlparse

TIER1_SUFFIXES = (
    # Kazakhstan: laws, statistics, government, national science
    "adilet.zan.kz", "stat.gov.kz", "gov.kz", "egov.kz", "akorda.kz", "parlam.kz",
    "primeminister.kz", "nationalbank.kz", "edu.gov.kz",
    # International primary / scholarly
    "doi.org", "crossref.org", "who.int", "un.org", "worldbank.org", "imf.org",
    "nih.gov", "nasa.gov", "europa.eu", "unesco.org", "oecd.org",
    "nature.com", "science.org", "thelancet.com", "nejm.org", "cell.com",
    "springer.com", "sciencedirect.com", "wiley.com", "arxiv.org", "aclanthology.org",
)
TIER1_TLD_HINTS = (".gov", ".edu", ".gov.kz", ".edu.kz", ".ac.uk", ".gov.uk")

TIER2_SUFFIXES = (
    "wikipedia.org", "wikidata.org", "britannica.com", "e-history.kz", "bigenc.ru",
    "kaznu.kz", "nu.edu.kz", "enu.kz", "openalex.org", "semanticscholar.org",
    "pubmed.ncbi.nlm.nih.gov", "scholar.archive.org", "archive.org",
)

TIER3_SUFFIXES = (
    "kazinform.kz", "inform.kz", "tengrinews.kz", "zakon.kz", "informburo.kz",
    "kapital.kz", "forbes.kz", "vlast.kz", "kursiv.media", "azattyq.org", "khabar.kz",
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "theguardian.com",
    "nytimes.com", "ria.ru", "tass.ru", "interfax.ru", "rbc.ru", "kommersant.ru",
)

TIER4_LOW = (
    "reddit.com", "quora.com", "otvet.mail.ru", "pikabu.ru", "vk.com", "vk.ru", "ok.ru", "dzen.ru",
    "facebook.com", "threads.net", "pinterest.com", "livejournal.com",
    "instagram.com", "tiktok.com", "youtube.com", "t.me", "x.com", "twitter.com",
    "fandom.com", "medium.com", "znanija.com", "brainly.com",
)


def domain_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _matches(host: str, suffixes: tuple[str, ...]) -> bool:
    return any(host == s or host.endswith("." + s) for s in suffixes)


def tier_of(url: str) -> int:
    host = domain_of(url)
    if not host:
        return 4
    if _matches(host, TIER4_LOW):
        return 4
    if _matches(host, TIER1_SUFFIXES) or any(host.endswith(t) for t in TIER1_TLD_HINTS):
        return 1
    if _matches(host, TIER2_SUFFIXES):
        return 2
    if _matches(host, TIER3_SUFFIXES):
        return 3
    return 4


# Sites that republish Wikipedia articles: the same text, so never an independent confirmation.
WIKI_MIRRORS = (
    "wikiwand.com", "ruwiki.ru", "wiki2.org", "wiki2.wiki", "wikizero.com", "wikimili.com",
    "wiki5.ru", "wikibrief.org", "dbpedia.org",
)


def registrable_domain(url: str) -> str:
    """The independent source behind a URL: sub-domains collapse (ru. and kk.wikipedia.org are one
    source) and Wikipedia mirrors count as wikipedia.org."""
    host = domain_of(url)
    if _matches(host, WIKI_MIRRORS):
        return "wikipedia.org"
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"gov", "edu", "com", "org", "ac", "co"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


# The open web search skips Wikipedia (fetched free from its own API), its mirrors and low-trust sites.
SEARCH_EXCLUDE = ("wikipedia.org",) + WIKI_MIRRORS + TIER4_LOW


def excluded_from_search(url: str) -> bool:
    return _matches(domain_of(url), SEARCH_EXCLUDE)


# The second web search is limited to trusted sites picked for the claim type.
_KZ_OFFICIAL = ["gov.kz", "akorda.kz", "parlam.kz", "adilet.zan.kz", "stat.gov.kz", "nationalbank.kz"]
_REFERENCE = ["e-history.kz", "bigenc.ru", "britannica.com"]
_INTERNATIONAL = ["un.org", "who.int", "worldbank.org", "imf.org", "oecd.org", "unesco.org"]
_SCIENCE = ["nature.com", "science.org", "nih.gov", "thelancet.com", "nejm.org", "sciencedirect.com",
            "springer.com", "arxiv.org"]
_NEWS = list(TIER3_SUFFIXES)

TRUSTED_FOR_TYPE: dict[str, list[str]] = {
    "law": ["adilet.zan.kz", "parlam.kz", "akorda.kz", "gov.kz", "zakon.kz"],
    "number": ["stat.gov.kz", "nationalbank.kz", "gov.kz", *_INTERNATIONAL, "kapital.kz", "forbes.kz",
               "kursiv.media", "kazinform.kz"],
    "citation": [*_SCIENCE, "aclanthology.org", "who.int"],
}
TRUSTED_DEFAULT = [*_REFERENCE, *_KZ_OFFICIAL, *_INTERNATIONAL, *_SCIENCE, *_NEWS]


def trusted_domains(claim_type: str) -> list[str]:
    return TRUSTED_FOR_TYPE.get(claim_type, TRUSTED_DEFAULT)
