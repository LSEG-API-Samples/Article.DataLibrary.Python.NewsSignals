"""
newsmetadata

High-level package for accessing and navigating LSEG News metadata
taxonomies in a Content-layer style API.

This package provides opinionated, user-friendly abstractions for:
- Enumerating metadata groups (e.g. Language, Geography)
- Retrieving RCS codes for a given taxonomy group
- Resolving individual metadata nodes by ID
- Navigating metadata hierarchies (children traversal)

Low-level REST endpoint access, bulk exports, and pagination mechanics
are intentionally not exposed at this layer. Users requiring full
endpoint flexibility should use the underlying transport or endpoint
interfaces directly.

Public API surface is intentionally small and explicit.
"""

# Expose the public API facade at the package level
from .metadata import metadata  # noqa: F401

__all__ = [
    "metadata",
]

__version__ = "0.1.0"

