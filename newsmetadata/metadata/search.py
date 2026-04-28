"""
News metadata search.

This module provides free-text search across News metadata taxonomy groups.
It fetches metadata entries, computes token-based relevance scores against
the specified fields, and returns results ranked by relevance.

Responsibilities:
- Fetch metadata entries for one or all taxonomy groups
- Score each entry against the search term
- Return ranked results as a DataFrame
"""

import re

import pandas as pd

from .enums import NewsMetadataGroup
from .codes import get_rcs_codes


def search_metadata(
    term: str,
    *,
    group: NewsMetadataGroup | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    min_relevance: float = 0.4,
    language: str | None = None,
) -> pd.DataFrame:
    """
    Search News metadata entries by free-text term.

    Fetches metadata codes for the specified group (or all groups when
    *group* is ``None``), scores every entry against *term* using the
    columns listed in *fields*, and returns the top *limit* results
    whose relevance meets the *min_relevance* threshold, ordered by
    descending relevance.

    Args:
        term: Free-text search query (e.g. "energy sector").
        group: Restrict to a single taxonomy group. When ``None``,
            all groups are searched.
        fields: Column names to match against.
            Defaults to ``["label", "description"]``.
        limit: Maximum number of results to return.
        min_relevance: Minimum relevance score (0–1) a result must
            reach to be included. Defaults to 0.4.
        language: Optional ``Accept-Language`` header value.

    Returns:
        pd.DataFrame with columns ``id``, ``label``, ``group``,
        ``description``, and ``relevance``, sorted by relevance
        descending.
    """
    if not isinstance(term, str) or not term.strip():
        raise ValueError("term must be a non-empty string")

    if fields is None:
        fields = ["label", "description"]

    # Determine which groups to query
    groups = [group] if group is not None else list(NewsMetadataGroup)

    # Fetch metadata for each group (concurrently when querying all)
    frames = _fetch_groups(groups, language)

    if not frames:
        return pd.DataFrame(columns=["id", "label", "group", "description", "relevance"])

    df = pd.concat(frames, ignore_index=True)

    if df.empty:
        return pd.DataFrame(columns=["id", "label", "group", "description", "relevance"])

    # Score each row against the search term
    df["relevance"] = df.apply(
        lambda row: _score(term, row, fields), axis=1
    )

    # Drop rows below the relevance threshold, sort, and limit
    df = (
        df[df["relevance"] >= min_relevance]
        .sort_values("relevance", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    # Return a consistent column set
    output_cols = ["id", "label", "group", "description", "relevance"]
    available = [c for c in output_cols if c in df.columns]
    return df[available]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_groups(
    groups: list[NewsMetadataGroup],
    language: str | None,
) -> list[pd.DataFrame]:
    """Fetch codes for a list of groups sequentially."""
    frames: list[pd.DataFrame] = []

    for g in groups:
        try:
            result = get_rcs_codes(g, language=language)
            if not result.empty:
                if "group" not in result.columns:
                    result["group"] = g.value
                frames.append(result)
        except Exception:
            # Skip groups that fail; partial results are still valuable.
            continue

    return frames


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*")


def _tokenize(text: str) -> list[str]:
    """Lowercase and split text into alphanumeric tokens."""
    return _TOKEN_RE.findall(text.lower())


def _strip_qualifiers(text: str) -> str:
    """Remove parenthetical suffixes like '(TRBC level 5)' before scoring."""
    return _PAREN_RE.sub(" ", text).strip()


def _score(term: str, row: pd.Series, fields: list[str]) -> float:
    """
    Compute a relevance score for *row* against *term*.

    The score combines three signals:
    1. **Query coverage** — what fraction of query tokens appear in the field.
    2. **Label precision** — penalises long, loosely-related labels by
       measuring `matched / field_tokens`.  A label "Energy" scores
       much higher than "Waste to Energy Systems & Equipment".
    3. **Substring bonus** — rewards fields where the raw query (or a
       large contiguous chunk) appears as-is, giving exact or
       near-exact matches a decisive boost.

    Parenthetical qualifiers (e.g. "(TRBC level 5)") are stripped
    before scoring so they don't dilute precision.

    Returns a value in [0, 1].
    """
    query_lower = term.lower().strip()
    query_tokens = _tokenize(query_lower)
    if not query_tokens:
        return 0.0

    best = 0.0

    for field in fields:
        value = row.get(field)
        if not isinstance(value, str) or not value:
            continue

        # Strip boilerplate qualifiers before scoring
        cleaned = _strip_qualifiers(value)
        field_lower = cleaned.lower()
        field_tokens = _tokenize(field_lower)

        if not field_tokens:
            continue

        field_token_set = set(field_tokens)

        # 1. Query coverage: fraction of query tokens found in the field
        matched = sum(1 for t in query_tokens if t in field_token_set)
        query_coverage = matched / len(query_tokens)

        # 2. Label precision: fraction of field tokens that are query hits
        #    Rewards concise, on-target labels over long tangential ones
        precision = matched / len(field_tokens)

        # 3. Substring / phrase bonus
        #    Full query as substring → large bonus
        #    Otherwise check each query token as substring for partial credit
        if query_lower in field_lower:
            substring_bonus = 1.0
        else:
            # partial: fraction of query tokens that appear as substrings
            sub_hits = sum(1 for t in query_tokens if t in field_lower)
            substring_bonus = 0.5 * (sub_hits / len(query_tokens))

        # Weighted combination
        score = round(
            0.35 * query_coverage
            + 0.35 * precision
            + 0.30 * substring_bonus,
            2,
        )

        if score > best:
            best = score

    return best
