"""Normalizer stage."""

from .base_stage import BaseStage


class NormalizerStage(BaseStage):
    """Normalization stage."""

    def run(self, context):
        """Normalize parsed and validated records."""
        raise NotImplementedError
