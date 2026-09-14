from __future__ import annotations

from typing import List
from aidoc_sdk.exceptions import AIDocValueError


# ---------------------------------------------------------------------------
# PDF Table Detection (Heuristic Layer)
# ---------------------------------------------------------------------------
# - Heuristic logic allowed here
# - Returns List[List[str]] for each table
# - No normalization
# - No hashing
# ---------------------------------------------------------------------------


def extract_tables_from_page(page) -> List[List[List[str]]]:
    """
    Returns list of tables.
    Each table is List[List[str]].
    """
    raw_tables = page.extract_tables() or []

    tables: List[List[List[str]]] = []

    for raw in raw_tables:
        if not raw:
            continue

        cleaned: List[List[str]] = []

        for row in raw:
            if row is None:
                continue

            cleaned_row = [(cell or "").strip() for cell in row]
            cleaned.append(cleaned_row)

        if cleaned:
            tables.append(cleaned)

    return tables
