"""Epa normalizer stub."""

from ...stages.normalizer import NormalizerStage


class EpaNormalizer(NormalizerStage):
    """Normalize provider records."""

    def run(self, context):
        """Implement provider-specific normalization."""
        raise NotImplementedError
