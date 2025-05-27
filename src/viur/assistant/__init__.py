"""
viur-assistant

AI-based assistance module plugin for ViUR
"""

from .bones.image import ImageBone, ImageBoneRelSkel
from .modules.assistant import Assistant
from .skeletons.assistant import AssistantSkel
from .config import CONFIG

__all__ = [
    "Assistant",
    "CONFIG",
    "ImageBone",
    "ImageBoneRelSkel",
]
