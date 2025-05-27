from viur.core.bones import *
from viur.core.skeleton import Skeleton


class AssistantSkel(Skeleton):
    anthropic_model = StringBone(
        descr="Model",
        params={"category": "Anthropic"},
        readOnly=True,
        defaultValue="claude-3-7-sonnet-20250219",
    )

    anthropic_max_tokens = NumericBone(
        descr="Maximum Tokens",
        params={"category": "Anthropic"},
        min=512,
        max=4096,
        readOnly=True,
        defaultValue=1024,
    )

    anthropic_max_thinking_tokens = NumericBone(
        descr="Maximum Thinking Tokens",
        params={"category": "Anthropic"},
        min=0,
        max=64000,
        readOnly=True,
        defaultValue=0,
    )

    anthropic_temperature = NumericBone(
        descr="Temperature",
        params={"category": "Anthropic"},
        precision=1,
        min=0,
        max=1,
        readOnly=True,
        defaultValue=1.0,
    )
    anthropic_system_prompt = TextBone(
        descr="Systemprompt",
        readOnly=True,
        params={"category": "Anthropic"},
        defaultValue="You are a coding-assistant that helps develop python-code for accessing a viur-backend. You only output json-strings containing a single key named \"code\".",
    )
    anthropic_api_key = CredentialBone(
        descr="API Key",
        readOnly=True,
        params={"category": "Anthropic"},
    )

    openai_model = StringBone(
        descr="Model",
        params={"category": "OpenAi"},
        readOnly=True,
        defaultValue="gpt-4o-mini",
    )

    openai_api_key = StringBone(
        descr="API Key",
        readOnly=False,
        params={"category": "OpenAi"},
    )
