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
    "reddit.com", "quora.com", "otvet.mail.ru", "pikabu.ru", "vk.com", "facebook.com",
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


def registrable_domain(url: str) -> str:
    """Collapse sub-domains so ru.wikipedia.org and kk.wikipedia.org count as ONE independent source."""
    host = domain_of(url)
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"gov", "edu", "com", "org", "ac", "co"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


# Extra, targeted searches for claim types where Kazakhstan has an official primary source.
TYPE_DOMAINS: dict[str, list[str]] = {
    "law": ["adilet.zan.kz"],
    "number": ["stat.gov.kz", "gov.kz"],
}
