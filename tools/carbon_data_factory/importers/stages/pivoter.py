"""Pivoter stage."""

from .base_stage import BaseStage


class PivoterStage(BaseStage):
    """Pivoting stage."""

    def run(self, context):
        """Pivot records as required by the provider."""
        raise NotImplementedError
