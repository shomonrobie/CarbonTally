"""Change detection logic."""

def detect_changes(before, after):
    """Return changed fields between two dictionaries."""
    changes = {}

    for key in set(before) | set(after):
        if before.get(key) != after.get(key):
            changes[key] = {"before": before.get(key), "after": after.get(key)}

    return changes
