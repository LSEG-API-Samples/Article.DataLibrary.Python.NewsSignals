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
from .children import get_children
from .enums import NewsMetadataGroup

class MetadataAPI:
    """
    Facade object providing access to News metadata functionality.

    This class intentionally exposes only high-level, intent-based
    operations and hides REST endpoint mechanics.
    """

    def codes(self, *, group: NewsMetadataGroup, language: str | None = None) -> pd.DataFrame:
        """
        Retrieve all metadata entries for a given taxonomy group.

        Args:
            group (NewsMetadataGroup): The metadata taxonomy group to enumerate.

        Returns:
            pd.Dataframe: Collection of metadata nodes belonging to the requested group.
        """
        return get_rcs_codes(group, language=language)

    def nodes(self, rcs_code: Union[str, Sequence[str]], *, language: str | None = None) -> pd.DataFrame:
        
        """
        Resolve a single metadata node by its identifier.

        Args:
            metadata_id (str): Metadata identifier (e.g. 'G:123', 'Topic:ABC').

        Returns:
            pd.Dataframe: The resolved metadata node.

        """
        return get_rcs_nodes(rcs_code, language=language)

    def children(self, rcs_code: str, *, language: str | None = None) -> pd.DataFrame:
        """
        Retrieve all child metadata nodes for a given parent metadata ID.

        Pagination and traversal mechanics are handled internally
        and are not exposed to the caller.

        Args:
            metadata_id (str): Parent metadata identifier.
        """
        return get_children(rcs_code, language=language)

# Singleton-style public entry point
metadata = MetadataAPI()
