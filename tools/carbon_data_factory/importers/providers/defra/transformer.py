"""Defra transformer stub."""

from ...stages.transformer import TransformerStage


class DefraTransformer(TransformerStage):
    """Transform provider records."""

    def run(self, context):
        """Implement provider-specific transformation."""
        raise NotImplementedError
