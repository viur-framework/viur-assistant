<div align="center">
    <!-- TODO: <img src="https://github.com/viur-framework/viur-artwork/raw/main/icons/icon-assistant.svg" height="196" alt="A hexagonal logo of Assistant" title="Assistant logo"/> -->
    <h1>viur-assistant</h1>
    <a href="https://pypi.org/project/viur-assistant/">
        <img alt="Badge showing current PyPI version" title="PyPI" src="https://img.shields.io/pypi/v/viur-assistant">
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/github/license/viur-framework/viur-assistant" alt="Badge displaying the license" title="License badge">
    </a>
    <br>
    AI-based <a href="https://www.viur.dev">ViUR</a> assistant plugin.
</div>

## Usage

### Install with pip

```
pip install viur-assistant
```

### Install with pipenv

```
pipenv install viur-assistant
```

### Register module

Import the `Assistant` module in the module loader in your project.

```python
# deploy/modules/__init__.py
from viur.assistant import Assistant as assistant  # noqa
```

_**Note**: the `# noqa` prevents your IDE from removing the import for refactorings,
as this is considered unnecessary (in this file)._

### Configuration

Import the assistant `CONFIG` in your project and set up the API keys.

```python
# deploy/main.py
from viur.core import secret
from viur.assistant import CONFIG as ASSISTANT_CONFIG

ASSISTANT_CONFIG.api_openai_key = "..."
ASSISTANT_CONFIG.api_anthropic_key = secret.get("api-anthropic-key")
```

_**Note:** Using the Google Secret Manager is the more secure way.
But of course the value can also be loaded from the env
— as long as the value is provided as a string._

## Development / Contributing

Create a fork and clone it

### Setup & Run tests

1. Install viur-assistant as editable in your project.
   ```sh
   cd my-project
   pip install -e path/to/viur-assistant[testing]
   cd path/to/viur-assistant
   ```
2. Launch the local development server
3. Get a valid session cookie and store it in the environment
   ```sh
   export SESSION_COOKIE="viur_cookie_$project=abc***xyz"
   ```
   This is necessary because the Assistant API is only accessible to admins.
4. Run the tests with pytest
   ```sh
   pytest tests -s
   ```

### Branches

Depending on what kind of change your Pull Request contains, please submit your PR against the following branches:

* **main:**
  fixes/patches that fix a problem with existing code go into this branch.
* **develop:**
  new features, refactorings, or adjustments for new versions of dependencies are added to this branch.
