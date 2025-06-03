import base64
import io
import json
import os
import typing as t
from json import JSONDecodeError

import PIL
import anthropic
import openai
from openai.types import ChatModel
from openai.types.chat import ChatCompletionMessageParam
from viur.core import conf, current, errors, exposed, utils
from viur.core.decorators import access
from viur.core.prototypes import List, Singleton, Tree

from ..config import ASSISTANT_LOGGER, CONFIG

logger = ASSISTANT_LOGGER.getChild(__name__)


class Assistant(Singleton):
    """
    Provides LLM-powered utilities within a ViUR module context.

    This class includes various AI-assisted features such as script generation,
    image description, and language-aware prompting. It is designed to be used
    in the context of a ViUR admin and integrates with services like
    OpenAI and Anthropic.

    Responsibilities:
      - Generating backend scripts from user instructions and data models.
      - Producing accessible image descriptions (e.g., for alt attributes).
      - Translate text.
      - Managing prompt and API settings.

    Integrated Services:
      - OpenAI (e.g., GPT) for image description generation and translations.
      - Anthropic Claude for structured script generation with reasoning capabilities.

    Configuration can be made in
     - this singleton skel itself.
     - The backend configuration `CONFIG`.

    .. note::
       The methods in this module assumes a properly configured environment
       with API keys and AI model settings. However, you only need to
       configure what is actually used.
       Error handling is included for common failure modes such as
       misconfiguration or service unavailability.
    """

    @exposed
    @access("user-view")
    # TODO: @force_post
    def generate_script(
        self,
        *,
        prompt: str,
        modules_to_include: list[str] = None,
        enable_caching: bool = False,
        max_thinking_tokens: int = 0
    ):
        """
        Generates a script based on a user prompt and optional module structures using a language model.

        This method builds a structured prompt for the LLM Anthropic Claude and optionally includes
        application-specific module metadata to enrich the generation context. Additional configuration
        such as caching behavior and token budgeting for "thinking steps" can be provided.

        :param prompt: The main user instruction or query that guides the script generation.

        :param modules_to_include: Optional list of module names whose structures
            should be included as part of the model context.
            These are injected into the LLM prompt as JSON.
        :param enable_caching: If set to True, instructs the system to use ephemeral caching for the
            scriptor documentation prompt section.
        :param max_thinking_tokens: If greater than 0, enables the model's "thinking" feature with a
            token budget for intermediate reasoning or planning steps.
        :return: A JSON-encoded string of the model's response, typically containing the generated script.

        :raises InternalServerError:
          - If configuration (`skel`) is missing.
          - If the LLM request fails due to connection or model errors.

        .. note::
         - Requires a valid `anthropic_model` configuration in the current context.
         - The actual parsing of the generated code (e.g., extracting specific script content)
           is currently marked as a TODO and has to be discussed.
        """

        kindName: t.Final[str] = "viur-assistant"

        if not (skel := self.getContents()):
            raise errors.InternalServerError(descr="Configuration missing")

        llm_params = {
            "model": skel["anthropic_model"],
            "max_tokens": skel["anthropic_max_tokens"] + max_thinking_tokens,
            "temperature": skel["anthropic_temperature"],
            "system": [{
                "type": "text",
                "text": skel["anthropic_system_prompt"]
            }],
            "messages": [{
                "role": "user",
                "content": (user_content := []),
            }]
        }

        # add docs to system prompt (with or without caching), should be delivered by scriptor package
        scriptor_doc_system_param = {
            "type": "text",
            "text": "",  # TODO: scriptor docs
        }
        # TODO: llm_params["system"].append(scriptor_doc_system_param)
        if enable_caching:
            scriptor_doc_system_param["cache_control"] = {"type": "ephemeral"}

        # thinking configuration
        if max_thinking_tokens > 0:
            llm_params["thinking"] = {
                "type": "enabled",
                # TODO: "budget_tokens": min(max_thinking_tokens, skel["anthropic_max_thinking_tokens"])
                "budget_tokens": max_thinking_tokens,
            }

        # add module structures
        if modules_to_include is not None and (structures := self.get_viur_structures(modules_to_include)):
            user_content.append({
                "type": "text",
                "text": json.dumps({
                    "module_structures": structures
                }, indent=2)
            })

        # finally, append user prompt
        user_content.append({
            "type": "text",
            "text": prompt
        })

        anthropic_client = anthropic.Anthropic(api_key=CONFIG.api_anthropic_key)
        logger.debug(f"{llm_params=}")
        try:
            message = anthropic_client.messages.create(**llm_params)
        except Exception as e:
            logger.exception(e)
            raise errors.InternalServerError(descr=str(e))
        logger.debug(f"{message=}")
        current.request.get().response.headers["Content-Type"] = "application/json"
        return message.model_dump_json()  # TODO: parse real "code" value

    def get_viur_structures(self, modules_to_include: t.Iterable[str]) -> dict[str, dict]:
        structures_from_viur = {}
        for module_name in modules_to_include:
            module = getattr(conf.main_app.vi, module_name, None)
            if not module:
                continue
            if isinstance(module, List):
                if module_name not in structures_from_viur:
                    structures_from_viur[module_name] = module.structure()
            elif isinstance(module, Tree):
                if module_name not in structures_from_viur:
                    structures_from_viur[module_name] = {
                        "node": module.structure(skelType="node"),
                        "leaf": module.structure(skelType="leaf")
                    }
            else:
                raise ValueError(
                    f"The ViUR-module must be of type 'Tree' or 'List'. "
                    f"{module!r} is (currently) unsupported."
                )
        return structures_from_viur

    @exposed
    @access("user-view")
    # TODO: @force_post
    def translate(
        self,
        *,
        text: str,
        language: str,
        simplified: bool = False,
        characteristic: t.Optional[str] = None,
    ):
        if simplified:
            if characteristic is not None:
                raise errors.BadRequest("Cannot use parameter *simplified* and *characteristic* at the same time")
            logger.warning('simplified is deprecated, use characteristic="simplified" instead')
            characteristic = "simplified"

        if not (skel := self.getContents()):
            raise errors.InternalServerError(descr="Configuration missing")

        characteristics = [
            *CONFIG.translate_language_characteristics.get("*", []),
            *CONFIG.translate_language_characteristics.get(characteristic, []),
        ]

        message = self.openai_create_completion(
            model=skel["openai_model"],
            messages=[{  # type: ignore (typed dict)
                "role": "user",
                "content": (
                    f"Translate the following text into {CONFIG.language_map.get(language, language)}"
                    f" ({". ".join(characteristics)})"
                    f" and only return the translation, keep HTML-tags: {text}\n"
                )
            }],
        )

        return self.render_text(message)

    @exposed
    @access("user-view")
    def describe_image(
        self,
        filekey: str,
        prompt: str = "",
        context: str = "",
        language: str | None = None,
    ):
        if not (skel := self.getContents()):
            raise errors.InternalServerError(descr="Configuration missing")

        if language is None:
            language = current.language.get()

        blob, mime = conf.main_app.file.read(key=filekey)
        if not blob:
            raise errors.NotFound(f"File not found with {filekey=!r}")

        resized_image_bytes = self._get_resized_image_bytes(
            image=blob,
            target_pixel_count=CONFIG.describe_image_pixel_default,
            jpeg_quality=CONFIG.describe_image_jpeg_quality_default,
        )
        base64_image = base64.b64encode(resized_image_bytes).decode("utf-8")

        context_prompt = ""
        if context or prompt:
            context_prompt = (
                f"Use the following data as additional information to describe the image:\n"
                # TODO: ??? f" {re.sub(r"[^a-zA-Z0-9 _-]", "", context)}\n\n"
                f" {prompt}\n\n{context}"
            )

        content = [
            {
                "type": "text",
                "text": (
                    f"Analyze the image and generate an appropriate HTML alt attribute"
                    f" in language: {CONFIG.language_map.get(language, language)}."
                    f" Provide only the plain text for the alt attributes without quotes and label.\n\n"
                    f"{context_prompt}\n"
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    # "url": "http://some-domain.com/image.jpeg",
                    "detail": "low",
                    # "low" = 85 Tokens, "high" = calulated differently
                    # "low" = resize (on openapis side) to < 512x512px
                    # https://platform.openai.com/docs/guides/images?api-mode=chat#calculating-costs
                },
            },
        ]

        message = self.openai_create_completion(
            model=skel["openai_model"],
            messages=[{  # type: ignore (typed dict)
                "role": "user",
                "content": content,
            }],
        )
        return self.render_text(message)

    def _get_resized_image_bytes(
        self,
        image: t.IO[bytes] | str | bytes | "os.PathLike[str]" | "os.PathLike[bytes]",
        target_pixel_count: int,
        jpeg_quality: int = 50,
    ):
        """
        Resize an image to approximately match a target total pixel count and return it as a JPEG byte stream.

        The image is scaled proportionally to meet the target pixel count (width × height),
        while preserving the original aspect ratio. If the resized dimensions would exceed
        the original image size, no upscaling is performed. The result is encoded as a JPEG.

        :param image: Input image, provided as a file-like object, byte string, file path, or raw bytes.
        :param target_pixel_count: Desired total number of pixels for the resized image.
            Used to compute the new dimensions.
        :param jpeg_quality: JPEG compression quality (0 to 100).
            Higher values yield better image quality at the cost of file size. Default is 50.
        :return: The resized and JPEG-compressed image as a byte stream.

        :raises ValueError: If `jpeg_quality` is not in the 0–100 range or the image input is invalid.

        .. note::
         - Images in PNG, SVG, or WEBP format are automatically converted to RGB JPEG.
         - This function is intended for preprocessing images before passing them to
           AI models, balancing detail and data size.
        """
        if not (0 <= jpeg_quality <= 100):
            raise ValueError("jpeg_quality must be between 0 and 100")

        if isinstance(image, bytes):
            image = io.BytesIO(image)
        if not isinstance(image, (io.TextIOBase, io.BufferedIOBase, io.RawIOBase, io.IOBase)):
            raise ValueError("image must be file-like or bytes")

        pillow_image = PIL.Image.open(image)
        if pillow_image.format in ["PNG", "SVG", "WEBP"]:  # TODO: ???
            jpeg_image = io.BytesIO()
            pillow_image.convert("RGB").save(jpeg_image, "JPEG")
            jpeg_image.seek(0)
            pillow_image = PIL.Image.open(jpeg_image)

        original_img_total_pixels = pillow_image.width * pillow_image.height
        side_ratio_to_n_pixels = (target_pixel_count / original_img_total_pixels) ** 0.5
        new_width = round(pillow_image.width * side_ratio_to_n_pixels)
        new_height = round(pillow_image.height * side_ratio_to_n_pixels)

        if new_height > pillow_image.height or new_width > pillow_image.width:
            resized_img = pillow_image
        else:
            resized_img = pillow_image.resize(
                (new_width, new_height),
                PIL.Image.Resampling.LANCZOS
            )

        result_bio = io.BytesIO()
        resized_img.save(result_bio, "jpeg", quality=jpeg_quality)
        result_bio.seek(0)
        return result_bio.read()

    def openai_create_completion(
        self,
        *,
        model: str | ChatModel,
        messages: t.Iterable[ChatCompletionMessageParam],
        **kwargs
    ):
        """
        Creates a model response in a new chat conversation.

        Uses OpenAI API and structured JSON format,
        see https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses#json-mode .

        :param model: Model ID used to generate the response, like gpt-4o or o3.
        :param messages: A list of messages comprising the conversation.
        :param kwargs: Additional arguments passing to the client.
        :return: The response in plain text on success.

        :raises errors.HTTPException: If an API error occurs.
        """
        client = openai.Client(api_key=CONFIG.api_openai_key)
        try:
            response = client.chat.completions.create(  # type: ignore
                model=model,
                messages=messages,
                n=kwargs.pop("n", 1),  # How many chat completion choices
                stop=kwargs.pop("stop", None),
                response_format=kwargs.pop("response_format", {  # type: ignore (typed dict)
                    "type": "json_schema",
                    "json_schema": {
                        "name": "viur-assistant",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "answer": {"type": "string"}
                            },
                            "required": ["answer"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }),
                **kwargs
            )
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API error: {e}")
            raise errors.ServiceUnavailable(descr=str(e)) from e
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API rate-limit reached: {e}")
            current.request.get().response.headers["Retry-After"] = e.response.headers.get("Retry-After", "60")
            raise errors.HTTPException(status=e.status_code, name=e.code, descr=str(e)) from e
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API error: [{e.status_code} {e.code}] {e}")
            raise errors.HTTPException(status=e.status_code, name=e.code, descr=str(e)) from e

        logger.debug(f"{response=}")
        try:
            message = json.loads(response.choices[0].message.content)
            message = message["answer"]
        except (JSONDecodeError, KeyError):
            raise errors.InternalServerError("Got invalid JSON from API")
        return message

    def render_text(self, text: str) -> t.Any:
        """
        Render the give text as usual for the current renderer.

        If the current renderer is the JSON renderer, JSON string is returned
        and the content-type header is also set to JSON.

        :param text: The text to render.
        """
        if utils.string.is_prefix(self.render.kind, "html"):
            current.request.get().response.headers["Content-Type"] = "text/html; charset=utf-8"
            return text
        elif utils.string.is_prefix(self.render.kind, "json"):
            current.request.get().response.headers["Content-Type"] = "application/json; charset=utf-8"
            return json.dumps(text)
        raise errors.NotImplemented(f"{self.render.kind} rendering not implemented")


Assistant.json = True
Assistant.html = True

# Enforce AssistantSkel is loaded and initialized anywhere
from ..skeletons.assistant import AssistantSkel  # noqa
