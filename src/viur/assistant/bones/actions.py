"""
Bone Actions

This module defines identifiers as they are used in vi-admin
to activate certain additional actions on a bone.

Examples:
~~~~~~~~~

    .. code-block:: python

        descr = TextBone(
            languages=["de", "en"],
            params={
                BONE_ACTION_KEY: [BoneAction.TRANSLATE],
            },
        )

        descr = ImageBone(
            params={
                BONE_ACTION_KEY: [BoneAction.DESCRIBE_IMAGE],
            },
        )
"""

import typing as t

BONE_ACTION_KEY: t.Final[str] = "actions"
"""The key of the parameter"""


class BoneAction:
    TRANSLATE: t.Final[str] = "translate"
    """Translate text"""

    DESCRIBE_IMAGE: t.Final[str] = "describe_image"
    """Describe image with an alt text"""
