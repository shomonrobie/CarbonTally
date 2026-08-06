"""Epa validator stub."""

from ...stages.validator import ValidatorStage


class EpaValidator(ValidatorStage):
    """Validate provider records."""

    def run(self, context):
        """Implement provider-specific validation."""
        raise NotImplementedError
