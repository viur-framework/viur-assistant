import typing as t

from viur.core import conf, i18n
from viur.core.bones import FileBone, StringBone
from viur.core.skeleton import RelSkel

from .actions import *

__all__ = [
    "ImageBone",
    "ImageBoneRelSkel",
]


class ImageBoneRelSkel(RelSkel):
    """
    RelSkel designed to use as using skeleton in a ``ImageBone``.
    """

    alt = StringBone(
        descr=i18n.translate("viur.assistant.imagebone.alt.descr", "Alternative text", public=True),
        searchable=True,
        languages=conf.i18n.available_languages,
        max_length=1024,
    )


class ImageBone(FileBone):
    """
    A specialized ``FileBone`` for image files.

    This bone type extends ``FileBone`` by:

    - Restricting accepted MIME types to images (by default).
    - Has a using skel with an alt ``StringBone``.
    - Optionally enabling the *Describe Image* bone action, which allows AI to generate an alt-text or caption
      for the uploaded image via an admin-triggerable action.
    """

    type = FileBone.type + ".image"

    def __init__(
        self,
        *,
        using: t.Type[RelSkel] = ImageBoneRelSkel,
        validMimeTypes: None | t.Iterable[str] = ("image/*",),
        enable_describe_image: bool = True,
        **kwargs,
    ):
        """
        Initialize an ImageBone, a file-based bone specialized for handling image uploads.

        Optionally adds a bone action that allows AI-based image description (alt-text generation)
        to be triggered from within the admin interface.

        :param using: The relational skeleton class used for additional data of this image.
            Defaults to ``ImageBoneRelSkel``, including the alt ``StringBone``.
        :param validMimeTypes: A list of accepted MIME types. Defaults to only allow image types (``("image/*",)``).
        :param enable_describe_image: If ``True``, the bone will include the ``DESCRIBE_IMAGE`` bone action,
            allowing AI-assisted image description via the vi-admin UI.
        :param kwargs: Additional keyword arguments passed to the base ``FileBone``.
        """
        if enable_describe_image:
            params = kwargs.setdefault("params", {})
            params[BONE_ACTION_KEY] = [*params.get(BONE_ACTION_KEY, []), BoneAction.DESCRIBE_IMAGE]
        super().__init__(
            using=using,
            validMimeTypes=validMimeTypes,
            **kwargs,
        )
