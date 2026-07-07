from __future__ import annotations

from app.services.base import BaseTTSService

_registry: dict[str, BaseTTSService] = {}


def register(lang: str, service: BaseTTSService) -> None:
    """Register a TTS service under the given language code (e.g. 'am', 'en')."""
    _registry[lang] = service


def get(lang: str) -> BaseTTSService:
    """Return the service for the given language code.

    Raises KeyError if no service is registered for that language.
    """
    if lang not in _registry:
        raise KeyError(f"No TTS service registered for language: '{lang}'")
    return _registry[lang]


def all_languages() -> list[str]:
    """Return all registered language codes."""
    return list(_registry.keys())
