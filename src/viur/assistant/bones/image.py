import typing as t

from viur.core import conf, i18n
from viur.core.bones import FileBone, StringBone
from viur.core.skeleton import RelSkel


class ImageBoneRelSkel(RelSkel):
    alt = StringBone(
        descr=i18n.translate("viur.assistant.imagebone.alt.descr", "Alternative text", public=True),
        searchable=True,
        languages=conf.i18n.available_languages,
        max_length=1024,
    )


class ImageBone(FileBone):
    type = FileBone.type + ".image"

    def __init__(
        self,
        *,
        using: t.Type[RelSkel] = ImageBoneRelSkel,
        validMimeTypes: None | t.Iterable[str] = ("image/*",),
        **kwargs,
    ):
        super().__init__(
            using=using,
            validMimeTypes=validMimeTypes,
            **kwargs,
        )
