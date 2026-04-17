"""Namespace validation utilities for Borg."""

from __future__ import annotations

import re
from typing import Annotated, TypeAlias

from pydantic import StringConstraints

NAMESPACE_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
_NAMESPACE_RE = re.compile(NAMESPACE_PATTERN)

NamespaceStr: TypeAlias = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=63,
        pattern=NAMESPACE_PATTERN,
    ),
]


def normalize_namespace(value: str) -> str:
    """Validate and normalize a namespace identifier."""
    normalized = value.strip()
    if not _NAMESPACE_RE.fullmatch(normalized):
        raise ValueError(
            "Namespace must be 1-63 chars of lowercase letters, digits, or hyphens, "
            "and must start and end with an alphanumeric character"
        )
    return normalized
