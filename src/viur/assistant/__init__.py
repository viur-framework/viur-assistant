"""
viur-assistant

AI-based assistance module plugin for ViUR
"""

from .bones.image import ImageBone, ImageBoneRelSkel
from .modules.assistant import Assistant
from .skeletons.assistant import AssistantSkel
from .bones.actions import BONE_ACTION_KEY, BoneAction
from .config import CONFIG

__all__ = [
    "Assistant",
    "BONE_ACTION_KEY",
    "BoneAction",
    "CONFIG",
    "ImageBone",
    "ImageBoneRelSkel",
]
