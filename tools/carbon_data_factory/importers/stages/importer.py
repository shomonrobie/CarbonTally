"""Importer stage."""

from .base_stage import BaseStage


class ImporterStage(BaseStage):
    """Import stage."""

    def run(self, context):
        """Persist transformed records."""
        raise NotImplementedError
