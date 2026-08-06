"""Abstract base classes."""

from abc import ABC, abstractmethod


class BaseImporter(ABC):
    """Abstract base class for importers."""

    @abstractmethod
    def run(self) -> None:
        """Execute the import."""
        raise NotImplementedError
