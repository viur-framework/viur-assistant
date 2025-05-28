import base64
import io
import json
import re
import typing as t

import PIL
import anthropic
import openai
from viur.core import conf, current, errors, exposed
from viur.core.decorators import access
from viur.core.prototypes import List, Singleton, Tree

from ..config import ASSISTANT_LOGGER, CONFIG

logger = ASSISTANT_LOGGER.getChild(__name__)


class Assistant(Singleton):
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
        return message

    def get_viur_structures(self, modules_to_include):
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
                    f"""The module should should be a instance of "tree" or "list". "{module}" is unsupported.""")
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
            characteristic = "simplified"
            logger.warning('simplified is deprecated, use characteristic="simplified" instead')
            if characteristic is not None:
                raise errors.BadRequest("Cannot use parameter *simplified* and *characteristic* at the same time")

        if not (skel := self.getContents()):
            raise errors.InternalServerError(descr="Configuration missing")

        characteristics = [
            *CONFIG.translate_language_characteristics.get("*", []),
            *CONFIG.translate_language_characteristics.get(characteristic, []),
        ]

        openai.api_key = CONFIG.api_openai_key
        try:
            response = openai.chat.completions.create(
                model=skel["openai_model"],
                messages=[{  # type: ignore (typed dict)
                    "role": "user",
                    "content": (
                        f"Translate the following text into {CONFIG.language_map.get(language, language)}"
                        f" ({". ".join(characteristics)})"
                        f" and only return the translation, keep HTML-tags: {text}\n"
                    )
                }],
                n=1,
                stop=None,
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

        return response.choices[0].message.content

    @exposed
    @access("user-view")
    def describe_image(
        self,
        filekey: str,
        prompt: str = "",
        context: str = "",
        language: str = "de",
    ):
        if not (skel := self.getContents()):
            raise errors.InternalServerError(descr="Configuration missing")

        blob, mime = conf.main_app.file.read(key=filekey)

        if not blob:
            raise errors.NotFound(f"File not found with {filekey=!r}")

        resized_image_bytes = self._get_resized_image_bytes(blob)
        base64_image = base64.b64encode(resized_image_bytes).decode("utf-8")

        content = [
            {
                "type": "text",
                "text": (
                    f"Use the following JSON data as additional information to describe the image:"
                    f" {re.sub(r"[^a-zA-Z0-9 _-]", "", context)}\n\n"
                    f"{prompt}\n\n"
                    f"Analyze the image and generate an appropriate HTML alt attribute"
                    f" in language: {CONFIG.language_map.get(language, language)}."
                    f" Provide only the plain text for the alt attributes."
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

        openai.api_key = CONFIG.api_openai_key
        try:
            completion = openai.chat.completions.create(
                model=skel["openai_model"],
                messages=[{  # type: ignore (typed dict)
                    "role": "user",
                    "content": content,
                }],
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

        return completion.choices[0].message.content

    def _get_resized_image_bytes(
        self,
        image,
        target_pixel_count=100_000,
        jpeg_quality=50,
    ):
        # assert 0 <= jpeg_quality <= 100, "jpeg_quality must be between 0 and 100"
        if isinstance(image, bytes):
            image = io.BytesIO(image)

        if not isinstance(image, (io.TextIOBase, io.BufferedIOBase, io.RawIOBase, io.IOBase)):
            raise ValueError("image must be file-like or bytes")

        pillow_image = PIL.Image.open(image)
        if pillow_image.format in ["PNG", "SVG", "WEBP"]:
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


Assistant.json = True
