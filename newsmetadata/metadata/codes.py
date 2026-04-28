"""
News metadata RCS codes based on group specification.

This module handles retrieval of metadata entries scoped to a specific
taxonomy group (e.g. Language, Geography), with optional free-text
query filtering and relevance ranking.

It corresponds to the REST endpoint:
    /data/news/v1/metadata?group=<GroupName>

Responsibilities:
- Validate group input
- Execute group-scoped retrieval
- Normalize results into a DataFrame
- Optionally score and rank results by relevance to a query
"""
import re

from lseg.data.delivery import endpoint_request
import pandas as pd
from .enums import NewsMetadataGroup

# News metadata endpoint
ENDPOINT = 'https://api.refinitiv.com/data/news/v1/metadata?limit=100'

def get_rcs_codes(
    group: NewsMetadataGroup,
    *,
    query: str | None = None,
    language: str | None = None,
    limit: int = 20,
    min_relevance: float = 0.4,
) -> pd.DataFrame:
    """
    Retrieve News metadata RCS codes for a specific taxonomy group.

    When *query* is provided, results are scored against the query
    and returned ranked by relevance.

    Args:
        group (NewsMetadataGroup): Metadata taxonomy group to enumerate.
        query (str, optional): Free-text search query. When provided,
            results are scored and ranked by relevance.
        language (str): Optional language specifier. Default: en
        limit (int): Maximum results when query is provided. Defaults to 20.
        min_relevance (float): Minimum relevance score (0–1) when query
            is provided. Defaults to 0.4.

    Returns:
        Codes and associated values as a pd.DataFrame
    """

    # Collect query parameters for preparation...
    query_params = {}
    
    # Required parameters - group
    # Note: I've made this a requirement for this API for now - the backend does not impose these guardrails.
    if not isinstance(group, NewsMetadataGroup):
        raise TypeError(
            "group must be a NewsMetadataGroup enum value"
        )

    query_params["group"] = group.value
    
    # Prepare endpoint definition...
    definition = endpoint_request.Definition(
        url = ENDPOINT,
        query_parameters = query_params
    )

    if language is not None:
        definition.header_parameters = {"Accept-Language": language}    
    
    # Submit request
    # Responses are paged. The algorithm will collect and combine results into a final container.
    try:
        frames = []
        query_params = {}
        
        while True:
            response = definition.get_data()
        
            if not response.is_success:
                raise Exception(
                    f"HTTP Error. Code: {response.raw_status_code}. "
                    f"Reason: {response.raw_reason_phrase}\n{response.raw_text}"
                )
        
            raw = response.data.raw
        
            # Append current page
            frames.append(pd.DataFrame.from_records(raw.get("data", [])))
        
            # Get next cursor (if any)
            meta = raw.get("meta", {})
            cursor = meta.get("next")
        
            # Stop if no more pages
            if not cursor:
                break

            # Get next page...
            query_params["cursor"] = cursor
            definition.query_parameters = query_params
        
        # Final combined DataFrame
        df = pd.concat(frames, ignore_index=True)
        
    except Exception as e:
        raise RuntimeError(f"An error occurred: {str(e)}") from None

    # When query is provided, apply relevance scoring
    if query is not None:
        return _apply_query(df, query, limit=limit, min_relevance=min_relevance)

    return df


# ---------------------------------------------------------------------------
# Query scoring helpers (migrated from search.py)
# ---------------------------------------------------------------------------

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
       measuring `matched / field_tokens`.
    3. **Substring bonus** — rewards fields where the raw query (or a
       large contiguous chunk) appears as-is.

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

        cleaned = _strip_qualifiers(value)
        field_lower = cleaned.lower()
        field_tokens = _tokenize(field_lower)

        if not field_tokens:
            continue

        field_token_set = set(field_tokens)

        matched = sum(1 for t in query_tokens if t in field_token_set)
        query_coverage = matched / len(query_tokens)
        precision = matched / len(field_tokens)

        if query_lower in field_lower:
            substring_bonus = 1.0
        else:
            sub_hits = sum(1 for t in query_tokens if t in field_lower)
            substring_bonus = 0.5 * (sub_hits / len(query_tokens))

        score = round(
            0.35 * query_coverage
            + 0.35 * precision
            + 0.30 * substring_bonus,
            2,
        )

        if score > best:
            best = score

    return best


def _apply_query(
    df: pd.DataFrame,
    query: str,
    *,
    limit: int = 20,
    min_relevance: float = 0.4,
    fields: list[str] | None = None,
) -> pd.DataFrame:
    """Score, filter, and rank a DataFrame against a free-text query."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    if fields is None:
        fields = ["label", "description"]

    if df.empty:
        return df

    df = df.copy()
    df["relevance"] = df.apply(
        lambda row: _score(query, row, fields), axis=1
    )

    df = (
        df[df["relevance"] >= min_relevance]
        .sort_values("relevance", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    return df