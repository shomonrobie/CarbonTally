"""EpaParser stub."""

from ...stages.parser import ParserStage


class EpaParser(ParserStage):
    """Parse provider input."""

    def run(self, context):
        """Implement provider-specific parsing."""
        raise NotImplementedError
