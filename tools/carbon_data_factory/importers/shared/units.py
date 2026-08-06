"""Unit mapping utilities."""

UNIT_ALIASES = {}


def normalize_unit(value):
    """Normalize a unit string."""
    if not value:
        return None

    return UNIT_ALIASES.get(str(value).strip().lower(), str(value).strip())
