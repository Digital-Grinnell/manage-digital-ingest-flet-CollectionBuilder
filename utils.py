"""
Utilities for manage-digital-ingest-flet-CollectionBuilder
This module now uses common_dg_utilities for shared functionality.
"""

# Import all shared utilities from common package
from common_dg_utilities import (
    generate_unique_id,
    calculate_string_similarity,
    sanitize_filename,
    perform_fuzzy_search,
    perform_fuzzy_search_for_transcript,
    perform_fuzzy_search_batch,
    read_markdown,
    read_config,
    session_get,
    show_message,
    validate_csv_headings,
)

# Import additional modules needed by this app
import json  # For utils.json.load() compatibility
from thumbnail import generate_thumbnail

# Re-export everything for backward compatibility
__all__ = [
    "generate_unique_id",
    "calculate_string_similarity",
    "sanitize_filename",
    "perform_fuzzy_search",
    "perform_fuzzy_search_for_transcript",
    "perform_fuzzy_search_batch",
    "read_markdown",
    "read_config",
    "session_get",
    "show_message",
    "validate_csv_headings",
    "json",
    "generate_thumbnail",
]
