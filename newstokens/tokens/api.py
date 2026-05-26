"""
Public API facade for News token access.

This module defines the user-facing interface for interacting with
News token taxonomies via the desktop (Workspace) endpoints.

Responsibilities:
- Expose a small, explicit API surface
- Enforce high-level semantic constraints
- Delegate detailed behavior to internal modules
"""

import pandas as pd
from typing import Union, Sequence
from .enums import Source, TokenCategory
from .browse import get_tokens
from .resolve import resolve_rcs_codes, resolve_story_codes
from .children import get_children


class TokensAPI:
    """
    Facade object providing access to News token functionality.

    This class intentionally exposes only high-level, intent-based
    operations and hides REST endpoint mechanics.
    """

    def browse(
        self,
        *,
        category: TokenCategory,
        query: str | None = None,
        source: Source | None = None,
        limit: int | None = None,
        language: str | None = None,
    ) -> pd.DataFrame:
        """
        Browse tokens within a taxonomy category.

        Args:
            category (TokenCategory): The token category to browse.
            query (str, optional): Server-side text filter (e.g. "Africa").
                Filters against label, description, and alternativeLabels.
            source (Source, optional): Content source filter.
            limit (int, optional): Maximum total number of results to return.
                When None, all available results are returned.
            language (str, optional): Language code for localized results.

        Returns:
            pd.DataFrame: Tokens belonging to the requested category.
        """
        return get_tokens(
            category,
            query=query,
            source=source,
            limit=limit,
            language=language,
        )

    def resolve(
        self,
        rcs_code: Union[str, Sequence[str]],
        *,
        language: str | None = None,
    ) -> pd.DataFrame:
        """
        Resolve one or more RCS codes by identifier.

        Args:
            rcs_code (str | list): RCS code identifiers
                (e.g. 'B:227', 'G:31', 'Topic:CVRSY',
                 ['B:227', 'G:31']).
            language (str, optional): Language code for localized results.

        Returns:
            pd.DataFrame: Resolved metadata nodes.
        """
        return resolve_rcs_codes(rcs_code, language=language)

    def resolve_story(
        self,
        story_id: Union[str, Sequence[str]],
        *,
        language: str | None = None,
    ) -> pd.DataFrame:
        """
        Resolve metadata nodes from one or more story identifiers.

        Fetches each story, extracts its subject codes, then resolves
        those codes via the metadata endpoint.

        Args:
            story_id (str | list): One or more story identifiers
                (e.g. 'urn:newsml:reuters.com:20260424:nL1N4170JC:2').
            language (str, optional): Language code for localized results.

        Returns:
            pd.DataFrame: Resolved metadata nodes with a 'story_id' column.
        """
        return resolve_story_codes(story_id, language=language)

    def children(
        self,
        rcs_code: str,
        *,
        query: str | None = None,
        limit: int | None = None,
        language: str | None = None,
    ) -> pd.DataFrame:
        """
        Retrieve all child tokens for a given parent token ID.

        Pagination is handled internally and not exposed to the caller.

        Args:
            rcs_code (str): Parent token identifier (e.g. 'M:1', 'B:227').
            query (str, optional): Server-side text filter (e.g. "trending").
                Filters against label and related fields.
            limit (int, optional): Maximum total number of results to return.
                When None, all available results are returned.
            language (str, optional): Language code for localized results.

        Returns:
            pd.DataFrame: Child tokens belonging to the parent.
        """
        return get_children(rcs_code, query=query, limit=limit, language=language)


# Singleton-style public entry point
tokens = TokensAPI()
