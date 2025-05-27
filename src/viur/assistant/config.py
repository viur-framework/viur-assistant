import logging
import typing as t

from viur.core.config import ConfigType

ASSISTANT_LOGGER: logging.Logger = logging.getLogger("viur.assistant")


class AssistantConfig(ConfigType):
    """Configuration for viur-assistant plugin."""

    api_openai_key: str = None
    """API Key for OpenAi"""

    api_anthropic_key: str = None
    """API Key for Anthropic"""

    language_map: t.Dict[str, str] = {
        "de": "German",
        "de-x-simple": "Deutsch, einfache Sprache",
        "en": "English",
    }

    translate_language_characteristic: t.Iterable[str] = {
        "*": [
            "not vulgar",
        ],
        "simple": [
            "simplified",
            "short sentences",
            "one information per sentence",
            "simple words",
            "avoid negative language",
            "sentences should be active, not passive",
            "avoid subjunctive clause",
            "one sentence per line",
            "split compound nouns with hyphens",
        ]
    }


CONFIG: t.Final[AssistantConfig] = AssistantConfig(
    strict_mode=True,
)
"""
The viur-assistent config instance.
"""
