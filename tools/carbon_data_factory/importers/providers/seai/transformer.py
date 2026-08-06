"""Seai transformer stub."""

from ...stages.transformer import TransformerStage


class SeaiTransformer(TransformerStage):
    """Transform provider records."""

    def run(self, context):
        """Implement provider-specific transformation."""
        raise NotImplementedError
