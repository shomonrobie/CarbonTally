"""Base pipeline stage."""

from abc import ABC, abstractmethod


class BaseStage(ABC):
    """Abstract pipeline stage."""

    @abstractmethod
    def run(self, context):
        """Process context and return the updated context."""
        raise NotImplementedError
