"""
Public API facade for News metadata access.

This module defines the user-facing interface for interacting with
News metadata taxonomies in a Content-layer style API.

Responsibilities:
- Expose a small, explicit API surface
- Enforce high-level semantic constraints (e.g. group must be provided)
- Delegate detailed behavior to internal modules
"""

import pandas as pd
from typing import Union, Sequence
from .enums import NewsMetadataGroup
from .codes import get_rcs_codes
from .nodes import get_rcs_nodes
from .nodes import get_story_nodes
from .children import get_children

class MetadataAPI:
    """
    Facade object providing access to News metadata functionality.

    This class intentionally exposes only high-level, intent-based
    operations and hides REST endpoint mechanics.
    """

    def codes(
        self,
        *,
        group: NewsMetadataGroup,
        query: str | None = None,
        language: str | None = None,
        limit: int = 20,
        min_relevance: float = 0.4,
    ) -> pd.DataFrame:
        """
        Retrieve metadata entries for a given taxonomy group.

        When *query* is provided, results are scored and ranked by
        relevance to the search term.

        Args:
            group (NewsMetadataGroup): The metadata taxonomy group to enumerate.
            query (str, optional): Free-text search query (e.g. "energy markets").
                When provided, results are filtered and ranked by relevance.
            language (str, optional): Language code to filter results. Defaults to None.
            limit (int): Maximum results when query is provided. Defaults to 20.
            min_relevance (float): Minimum relevance score (0–1) when query
                is provided. Defaults to 0.4.

        Returns:
            pd.Dataframe: Collection of metadata nodes belonging to the requested group.
        """
        return get_rcs_codes(group, query=query, language=language, limit=limit, min_relevance=min_relevance)

    def nodes(self, rcs_code: Union[str, Sequence[str]], *, language: str | None = None) -> pd.DataFrame:
        
        """
        Resolve a single, or list, of metadata nodes by its identifier.

        Args:
            rcs_code (str|list): Metadata identifiers (e.g. 'G:123', 'Topic:ABC', ['G:123', 'R:219']).
            language (str, optional): Language code to filter results. Defaults to None.            

        Returns:
            pd.Dataframe: The resolved metadata nodes.

        """
        return get_rcs_nodes(rcs_code, language=language)

    def story_nodes(self, story_id: Union[str, Sequence[str]], *, language: str | None = None) -> pd.DataFrame:        
        
        """
        Resolve a list of metadata nodes based on a story identifier.

        Args:
            story_id (str): (e.g. 'urn:newsml:reuters.com:20260424:nL1N4170JC:2').
            language (str, optional): Language code to filter results. Defaults to None.            

        Returns:
            pd.Dataframe: The resolved metadata node.

        """
        return get_story_nodes(story_id, language=language)

    def children(self, rcs_code: str, *, language: str | None = None) -> pd.DataFrame:
        """
        Retrieve all child metadata nodes for a given parent metadata ID.

        Pagination and traversal mechanics are handled internally
        and are not exposed to the caller.

        Args:
            rcs_code (str): Parent metadata identifier.
            language (str, optional): Language code to filter results. Defaults to None.            
        """
        return get_children(rcs_code, language=language)

# Singleton-style public entry point
metadata = MetadataAPI()
