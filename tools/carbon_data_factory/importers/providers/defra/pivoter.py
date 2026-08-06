"""Defra pivoter stub."""

from ...stages.pivoter import PivoterStage


class DefraPivoter(PivoterStage):
    """Provider-specific pivoting logic."""

    def run(self, context):
        """Implement provider-specific pivoting."""
        raise NotImplementedError
