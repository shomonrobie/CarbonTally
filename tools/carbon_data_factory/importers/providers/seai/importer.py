"""Seai importer stub."""

from ...base_importer import BaseImporter


class SeaiImporter(BaseImporter):
    """Import provider records."""

    def run(self) -> None:
        """Implement provider-specific import."""
        raise NotImplementedError
