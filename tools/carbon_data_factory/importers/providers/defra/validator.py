"""Defra validator stub."""

from ...stages.validator import ValidatorStage


class DefraValidator(ValidatorStage):
    """Validate provider records."""

    def run(self, context):
        """Implement provider-specific validation."""
        raise NotImplementedError
