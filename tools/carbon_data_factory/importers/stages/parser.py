"""Parser stage."""

from .base_stage import BaseStage


class ParserStage(BaseStage):
    """Parsing stage."""

    def run(self, context):
        """Parse raw input into a structured payload."""
        raise NotImplementedError
