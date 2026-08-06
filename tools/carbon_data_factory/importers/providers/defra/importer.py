"""Defra importer stub."""

from ...base_importer import BaseImporter


class DefraImporter(BaseImporter):
    """Import provider records."""

    def run(self) -> None:
        """Implement provider-specific import."""
        raise NotImplementedError
