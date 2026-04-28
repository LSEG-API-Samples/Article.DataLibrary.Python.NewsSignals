"""
News metadata RCS codes based on group specification.

This module handles retrieval of metadata entries scoped to a specific
taxonomy group (e.g. Language, Geography).

It corresponds to the REST endpoint:
    /data/news/v1/metadata?group=<GroupName>

Responsibilities:
- Validate group input
- Execute group-scoped retrieval
- Normalize results into MetadataCollection
"""
from lseg.data.delivery import endpoint_request
import pandas as pd
from .enums import NewsMetadataGroup

# News metadata endpoint
ENDPOINT = 'https://api.refinitiv.com/data/news/v1/metadata?limit=100'

def get_rcs_codes(group: NewsMetadataGroup, *, language: str | None = None) -> pd.DataFrame:
    """
    Retrieve News metadata RCS codes for a specific taxonomy group.

    Args:
        group (NewsMetadataGroup): Metadata taxonomy group to enumerate.
        language (str): Optional language specifier. Default: en

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
        return pd.concat(frames, ignore_index=True)
        
    except Exception as e:
        raise RuntimeError(f"An error occurred: {str(e)}") from None