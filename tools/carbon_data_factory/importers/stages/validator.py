"""Validator stage."""

from .base_stage import BaseStage


class ValidatorStage(BaseStage):
    """Validation stage."""

    def run(self, context):
        """Validate parsed records."""
        raise NotImplementedError
