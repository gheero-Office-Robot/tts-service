from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTTSService(ABC):
    """Abstract base class for all language-specific TTS services."""

    ready: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """Load the model and any required assets. Called once at startup."""

    @abstractmethod
    def generate(self, text: str) -> bytes:
        """Synthesize speech from text and return raw WAV bytes."""
