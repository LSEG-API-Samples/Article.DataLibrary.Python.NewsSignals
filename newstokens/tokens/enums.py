"""
Enumerations for News token categories.

This module defines closed vocabularies used throughout the
tokens API to enforce correctness and prevent invalid inputs.
"""

from enum import Enum


class TokenCategory(Enum):
    """
    Supported News token categories.
    """

    BUSINESS_SECTORS = "businesssectors"
    COMMUNITY_SOURCES = "communitysources"
    GEOGRAPHIES = "geographies"
    LANGUAGES = "languages"
    MARKETS = "markets"
    MORE_TOPICS = "moretopics"
    ORGANIZATIONS = "organizations"
    REPORTS = "reports"
    SEARCH_AND_DISCOVER = "searchanddiscover"
    SOURCES = "sources"

    def __str__(self) -> str:
        return self.value


class Source(Enum):
    """
    Content source filters for News tokens.
    """

    NEWS_WIRE = "NewsWire"
    NEWS_ROOM = "NewsRoom"

    def __str__(self) -> str:
        return self.value
