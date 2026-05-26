"""
RCS code resolution.

This module resolves one or more News RCS codes given their identifiers,
using the RDP metadata endpoint which is accessible from both
platform (RDP) and desktop (Workspace) sessions.

It corresponds to the REST endpoint:
    /data/news/v1/metadata/{id}

Responsibilities:
- Validate RCS code input
- Resolve one or more RCS codes concurrently
- Normalize results into a DataFrame
"""

from lseg.data.content import news
from lseg.data.delivery import endpoint_request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Sequence
import pandas as pd

from .constants import (
    RCS_CODE_FIELD,
    STATUS_FIELD,
    ERROR_MESSAGE_FIELD,
)

# News metadata endpoint (shared with RDP)
ENDPOINT = "https://api.refinitiv.com/data/news/v1/metadata/{id}"


def resolve_rcs_codes(
    rcs_code: Union[str, Sequence[str]],
    *,
    language: str | None = None,
) -> pd.DataFrame:
    """
    Resolve one or more RCS codes by identifier.

    Args:
        rcs_code (str | list): One or more RCS code identifiers
            (e.g. 'G:123', 'Topic:ABC', ['B:227', 'G:31']).
        language (str, optional): Language code for Accept-Language header.

    Returns:
        pd.DataFrame: Resolved metadata nodes with status columns.
    """
    if language is not None and not isinstance(language, str):
        raise TypeError("language must be a string or None")

    # Normalize to a list and filter out empty values
    codes = [rcs_code] if isinstance(rcs_code, str) else list(rcs_code)
    codes = [c for c in codes if isinstance(c, str) and c.strip()]

    if not codes:
        return pd.DataFrame()

    # Fetch concurrently
    frames = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_single_node, code, language): code
            for code in codes
        }

        for future in as_completed(futures):
            code = futures[future]
            try:
                frames.append(future.result())
            except Exception as e:
                print(f"FAILED for {code}: {type(e).__name__}: {e}")
                continue

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def _fetch_single_node(rcs_code: str, language: str | None) -> pd.DataFrame:
    """Fetch a single RCS code from the metadata endpoint."""
    definition = endpoint_request.Definition(
        url=ENDPOINT,
        path_parameters={"id": rcs_code},
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


def resolve_story_codes(
    story_id: Union[str, Sequence[str]],
    *,
    language: str | None = None,
) -> pd.DataFrame:
    """
    Resolve metadata nodes from one or more story identifiers.

    For each story, fetches the story content, extracts subject codes,
    then resolves those codes via the metadata endpoint.

    Args:
        story_id (str | list): One or more story identifiers
            (e.g. 'urn:newsml:reuters.com:20260424:nL1N4170JC:2').
        language (str, optional): Language code for Accept-Language header.

    Returns:
        pd.DataFrame: Resolved metadata nodes with a 'story_id' column.
            Each row represents one (story, code) pair.
    """
    if language is not None and not isinstance(language, str):
        raise TypeError("language must be a string or None")

    # Normalize story ID to a list and filter out empty values
    ids = [story_id] if isinstance(story_id, str) else list(story_id)
    ids = [id for id in ids if isinstance(id, str) and id.strip()]

    if not ids:
        return pd.DataFrame()

    # Step 1: Fetch stories concurrently and extract subject codes
    story_codes = {}  # {story_id: [codes]}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_subject_codes, sid): sid
            for sid in ids
        }

        for future in as_completed(futures):
            sid = futures[future]
            try:
                codes = future.result()
                if codes:
                    story_codes[sid] = codes
            except Exception as e:
                print(f"FAILED for {sid}: {type(e).__name__}: {e}")
                continue

    if not story_codes:
        return pd.DataFrame()

    # Step 2: Invert mapping — {code: [story_id, ...]}
    code_to_stories = {}
    for sid, codes in story_codes.items():
        for code in codes:
            code_to_stories.setdefault(code, []).append(sid)

    # Step 3: Resolve unique codes in one bulk call
    unique_codes = list(code_to_stories.keys())
    resolved = resolve_rcs_codes(unique_codes, language=language)

    # Step 4: Expand back — one row per (story_id, code)
    rows = []
    for _, row in resolved.iterrows():
        code = row.get("rcs_code") or row.get("id")
        if code in code_to_stories:
            for sid in code_to_stories[code]:
                new_row = row.copy()
                new_row["story_id"] = sid
                rows.append(new_row)

    return pd.DataFrame(rows).reset_index(drop=True)


def _fetch_subject_codes(story_id: str) -> list[str]:
    """Fetch a story and return its subject codes."""
    story = news.story.Definition(story_id).get_data()
    return story.data.story.subject_codes
