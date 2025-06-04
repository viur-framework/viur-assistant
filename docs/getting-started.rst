Getting Started
===============

Install with pip
----------------

.. code-block:: bash

   pip install viur-assistant


Install with pipenv
-------------------

.. code-block:: bash

   pipenv install viur-assistant


Register module
---------------

Import the ``Assistant`` module in the module loader in your project.

.. code-block:: python

   # deploy/modules/__init__.py
   from viur.assistant import Assistant as assistant  # noqa

.. note::

   The ``# noqa`` prevents your IDE from removing the import for refactorings,
   as this is considered unnecessary (in this file).


Configuration
-------------

Import the assistant ``CONFIG`` in your project and set up the API keys.

.. code-block:: python

   # deploy/main.py
   from viur.core import secret
   from viur.assistant import CONFIG as ASSISTANT_CONFIG

   ASSISTANT_CONFIG.api_openai_key = "..."
   ASSISTANT_CONFIG.api_anthropic_key = secret.get("api-anthropic-key")

.. note::

   Using the Google Secret Manager is the more secure way.
   But of course the value can also be loaded from the env
   — as long as the value is provided as a string.
