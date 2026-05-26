"""
newstokens

High-level package for accessing and navigating LSEG News token
taxonomies via the desktop (Workspace) token endpoints.

This package provides opinionated, user-friendly abstractions for:
- Browsing tokens by category (e.g. geographies, markets)
- Resolving individual tokens by ID
- Navigating token hierarchies (children traversal)

Low-level REST endpoint access, bulk exports, and pagination mechanics
are intentionally not exposed at this layer.

Public API surface is intentionally small and explicit.
"""

from .tokens import tokens  # noqa: F401

__all__ = [
    "tokens",
]

__version__ = "0.1.0"
