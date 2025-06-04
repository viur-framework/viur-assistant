Bone Actions
============

This package is primarily intended to integrate AI-powered functionality
into the ViUR administrative interface (vi-admin).
To support seamless interaction within the admin UI,
it defines identifiers for so-called *Bone Actions* as expected by the admin.

Bone Actions are interactive tools and helpers that can be attached
to specific bones within edit form views in vi-admin.
By enabling AI-driven features—such as text translation or image description
as Bone Actions, users can conveniently trigger complex tasks
on individual bones without leaving the context of the admin interface.


Translate Action:
-----------------

Activates a translation tool for multilingual bones.

.. code-block:: python

    descr = TextBone(
        languages=["de", "en"],
        params={
            BONE_ACTION_KEY: [BoneAction.TRANSLATE],
        },
    )



Image Describe Action:
----------------------

Activates a description tool of alt-texts for images.

.. code-block:: python

    image = ImageBone(
        params={
            BONE_ACTION_KEY: [BoneAction.DESCRIBE_IMAGE],
        },
    )

