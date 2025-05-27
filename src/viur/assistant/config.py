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


CONFIG: t.Final[AssistantConfig] = AssistantConfig(
    strict_mode=True,
)
"""
The viur-assistent config instance.
"""
