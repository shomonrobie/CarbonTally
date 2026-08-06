"""Common validation functions."""

def is_non_empty(value):
    """Return True when value is not empty."""
    return bool(value and str(value).strip())
