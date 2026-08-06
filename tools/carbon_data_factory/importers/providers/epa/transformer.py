"""Epa transformer stub."""

from ...stages.transformer import TransformerStage


class EpaTransformer(TransformerStage):
    """Transform provider records."""

    def run(self, context):
        """Implement provider-specific transformation."""
        raise NotImplementedError
