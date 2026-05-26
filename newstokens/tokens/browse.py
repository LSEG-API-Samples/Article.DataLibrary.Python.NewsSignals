"""
News token browsing by category.

This module handles retrieval of tokens scoped to a specific
taxonomy category (e.g. geographies, markets), with optional
server-side query filtering.

It corresponds to the REST endpoint:
    /data/news/v1/tokens/{category}

Responsibilities:
- Validate category input
- Execute category-scoped retrieval
- Handle offset/limit pagination internally
- Normalize results into a DataFrame with selected columns
"""

from lseg.data.delivery import endpoint_request
import pandas as pd
from .enums import Source, TokenCategory
from .constants import BROWSE_COLUMNS

# News tokens endpoint
ENDPOINT = "https://api.refinitiv.com/data/news/v1/tokens/{category}"

# Base URL for constructing paginated requests
BASE_URL = "https://api.refinitiv.com/data/news/v1"


def get_tokens(
    category: TokenCategory,
    *,
    query: str | None = None,
    source: Source | None = None,
    limit: int | None = None,
    language: str | None = None,
) -> pd.DataFrame:
    """
    Retrieve News tokens for a specific taxonomy category.

    Args:
        category (TokenCategory): Token category to browse.
        query (str, optional): Server-side text filter against
            label, description, and alternativeLabels.
        source (Source, optional): Content source filter.
        limit (int, optional): Maximum total number of results to return.
            When None, all available results are returned.
        language (str, optional): Language code for Accept-Language header.

    Returns:
        pd.DataFrame: Tokens with selected columns.
    """
    if not isinstance(category, TokenCategory):
        raise TypeError("category must be a TokenCategory enum value")

    if source is not None and not isinstance(source, Source):
        raise TypeError("source must be a Source enum value")

    # Build query parameters
    query_params = {}

    if query is not None:
        query_params["query"] = query

    if source is not None:
        query_params["source"] = source.value

    # Prepare endpoint definition
    definition = endpoint_request.Definition(
        url=ENDPOINT,
        path_parameters={"category": category.value},
        query_parameters=query_params if query_params else None,
    )

    if language is not None:
        definition.header_parameters = {"Accept-Language": language}

    # Submit request
    # Responses are paged via offset/limit. Collect all pages into a single DataFrame.
    try:
        frames = []

        while True:
            response = definition.get_data()

            if not response.is_success:
                raise Exception(
                    f"HTTP Error. Code: {response.raw_status_code}. "
                    f"Reason: {response.raw_reason_phrase}\n{response.raw_text}"
                )

            raw = response.data.raw

            # Append current page
            page_data = raw.get("tokens", [])
            if page_data:
                frames.append(pd.DataFrame.from_records(page_data))

            # Check if we've reached the requested limit
            if limit is not None:
                total = sum(len(f) for f in frames)
                if total >= limit:
                    break

            # Get next page URL (if any)
            meta = raw.get("meta", {})
            next_url = meta.get("next")

            # Stop if no more pages
            if not next_url:
                break

            # Follow the next page URL
            definition = endpoint_request.Definition(
                url=f"{BASE_URL}{next_url}",
            )

            if language is not None:
                definition.header_parameters = {"Accept-Language": language}

        if not frames:
            return pd.DataFrame(columns=BROWSE_COLUMNS)

        # Combine all pages
        df = pd.concat(frames, ignore_index=True)

    except Exception as e:
        raise RuntimeError(f"An error occurred: {str(e)}") from None

    # Enforce the total result limit
    if limit is not None:
        df = df.head(limit)

    # Select and return only the columns we expose
    # Use reindex to handle any missing columns gracefully
    return df.reindex(columns=BROWSE_COLUMNS)
