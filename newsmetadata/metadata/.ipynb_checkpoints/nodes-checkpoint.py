"""
Single metadata node resolution.

This module resolves a single News metadata node given its identifier.

It corresponds to the REST endpoint:
    /data/news/v1/metadata/{id}

Responsibilities:
- Validate metadata ID format
- Resolve a single metadata node
- Normalize into a MetadataNode model
"""

from lseg.data.delivery import endpoint_request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Sequence
import pandas as pd

# News metadata endpoint
ENDPOINT = 'https://api.refinitiv.com/data/news/v1/metadata/{id}'

def get_rcs_nodes(rcs_code: Union[str, Sequence[str]], *, language: str | None = None) -> pd.DataFrame:
    """
    Retrieve a single metadata node by identifier.

    Args:
        metadata_id (str): Metadata identifier (e.g. 'G:123', 'Topic:ABC').

    Returns:
        MetadataNode: Resolved metadata node.

    Raises:
        LookupError: If the metadata ID does not exist.
        ValueError: If the metadata ID format is invalid.
    """
    # Ensure parameters are valid...
    if language is not None and not isinstance(language, str):
        raise TypeError("language must be a string or None")
    
    # Normalize to a list and filter out empty values
    codes = [rcs_code] if isinstance(rcs_code, str) else list(rcs_code)
    codes = [c for c in codes if isinstance(c, str) and c.strip()]

    # Capture the collection of data frames from each concurrent call with the thread pool
    frames = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_single_node, code, language): code
            for code in codes
        }

        # Iterate through each defined task...
        for future in as_completed(futures):
            frames.append(future.result())

    return pd.concat(frames, ignore_index=True)


from .constants import (
    RCS_CODE_FIELD,
    STATUS_FIELD,
    ERROR_MESSAGE_FIELD
)

def _fetch_single_node(rcs_code: str, language: str | None) -> pd.DataFrame:
    """Fetch a single RCS code."""
    definition = endpoint_request.Definition(
        url=ENDPOINT,
        path_parameters={"id": rcs_code}
    )

    if language is not None:
        definition.header_parameters = {"Accept-Language": language}
    
    response = definition.get_data()

    if not response.is_success:
        return pd.DataFrame([{
            RCS_CODE_FIELD: rcs_code,
            STATUS_FIELD: "error",
            ERROR_MESSAGE_FIELD: response.errors,
        }])

    df = pd.DataFrame([response.data.raw["newsCode"]])

    # Inject API-owned metadata columns
    df[RCS_CODE_FIELD] = rcs_code
    df[STATUS_FIELD] = "ok"
    df[ERROR_MESSAGE_FIELD] = None
    
    return df
