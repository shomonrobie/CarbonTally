"""Verifier stage."""

from .base_stage import BaseStage


class VerifierStage(BaseStage):
    """Verification stage."""

    def run(self, context):
        """Verify imported data."""
        raise NotImplementedError
