"""Transformer stage."""

from .base_stage import BaseStage


class TransformerStage(BaseStage):
    """Transformation stage."""

    def run(self, context):
        """Transform normalized records into the target shape."""
        raise NotImplementedError
