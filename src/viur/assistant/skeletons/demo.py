from viur.core.skeleton import Skeleton
from viur.core.bones import *
from bones.image import ImageBone

class DemoSkel(Skeleton):

    imagebonetest = ImageBone(descr="Image",params={"actions":[
        "describe_image"
    ]})

    descr = TextBone(
        descr="Beschreibung",
        languages=['de','en'],
        params={"actions":["translate"]}
    )