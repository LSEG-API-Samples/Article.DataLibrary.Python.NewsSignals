"""
Enumerations for News metadata.

This module defines closed vocabularies used throughout the
metadata API to enforce correctness and prevent invalid inputs.
"""

from enum import Enum

class NewsMetadataGroup(Enum):
    """
    Supported News metadata taxonomy groups.
    """

    BUSINESS_SECTORS = "BusinessSectors"
    GEOGRAPHY = "Geography"
    LANGUAGE = "Language"
    MARKET = "Market"
    MORE_TOPICS = "MoreTopics"
    REPORT = "Report"
    SOURCE = "Source"

    def __str__(self) -> str:
        return self.value
