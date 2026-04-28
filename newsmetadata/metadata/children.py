"""
Metadata hierarchy traversal.

This module retrieves child metadata nodes for a given parent metadata ID.

It corresponds to the REST endpoint:
    /data/news/v1/metadata/{id}/children

Pagination mechanics are handled internally and intentionally not exposed
to the public API.
"""

from lseg.data.delivery import endpoint_request
import pandas as pd

# News metadata endpoint
#ENDPOINT = 'https://api.refinitiv.com/data/news/v1/metadata/{id}/children?limit=50'
endpoint = 'https://api.refinitiv.com/data/news/v1'

cursor="/metadata/M%3AKW/children?offset=50&limit=50"

def get_children(rcs_code: str, *, language: str | None = None) -> pd.DataFrame:
    """
    Retrieve News metadata RCS codes for a specific taxonomy group.

    Args:
        group (NewsMetadataGroup): Metadata taxonomy group to enumerate.
        language (str): Optional language specifier. Default: en

    Returns:
        Codes and associated values as a pd.DataFrame
    """
    
    # Ensure parameters are valid...
    if language is not None and not isinstance(language, str):
        raise TypeError("language must be a string or None")
        
    if not isinstance(rcs_code, str):
        raise TypeError("RCS code is required and must be a string")
    
    # Prepare endpoint definition...
    url = f'/metadata/{rcs_code}/children?limit=100'

    definition = endpoint_request.Definition(
        url = f"{endpoint}{url}"
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
            url = meta.get("next")
        
            # Stop if no more pages
            if not url:
                break

            # Get next page...
            definition.url = f"{endpoint}{url}"
        
        # Final combined DataFrame
        return pd.concat(frames, ignore_index=True)
        
    except Exception as e:
        raise RuntimeError(f"An error occurred: {str(e)}") from None