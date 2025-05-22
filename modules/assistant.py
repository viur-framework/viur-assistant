from viur.core.prototypes import Singleton, List, Tree
from viur.core import errors, conf, db, exposed
from viur.core.decorators import access
from viur.core.modules.file import File
import json, base64, io, PIL, logging, re



try:
    import anthropic
except:
    anthropic = None

try:
    import openai
except:
    openai = None

class Assistant(Singleton):
    @exposed
    @access("user-view")
    def generate_script(self,
               prompt: str,
               modules_to_include:list[str]=None,
               enable_caching:bool=False,
               max_thinking_tokens:int=0
               ):
        if not anthropic:
            raise errors.BadGateway("Needed Dependencies are missing.")

        skel = self.viewSkel()
        key = db.Key(skel.kindName, self.getKey())

        if not skel.read(key):
            raise errors.NotFound()

        llm_params = {
            "model"      : skel['anthropic_model'],
            "max_tokens" : skel['anthropic_max_tokens'],
            "temperature": skel['anthropic_temperature'],
            "system"     : [{
                "type": "text",
                "text": skel['anthropic_system_prompt']
            }],
            "messages"   : [{
                "role"   : "user",
                "content": []
            }]
        }

        '''
        # add docs to system prompt (with or without caching), should be delivered by scriptor package
        scriptor_doc_system_param = {
            "type": "text",
            "text": scriptor_docs_txt_data,
        }
        '''
        scriptor_doc_system_param = {
            "type": "text",
            "text": ""#scriptor docs#todo
        }
        if enable_caching:
            scriptor_doc_system_param["cache_control"] = {"type": "ephemeral"}
        llm_params["system"].append(scriptor_doc_system_param)

        # thinking configuration
        if max_thinking_tokens > 0:
            llm_params["thinking"] = {
                "type"         : "enabled",
                "budget_tokens": skel['anthropic_max_thinking_tokens']
            }

        # add module structures
        if modules_to_include is not None:
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
                            "node": module.structure(skelType = "node"),
                            "leaf": module.structure(skelType = "leaf")
                        }
                else:
                    raise ValueError(
                        f"""The module should should be a instance of "tree" or "list". "{module}" is unsupported.""")

            selected_module_structures = {
                "module_structures": structures_from_viur}
            selected_module_structures_description = json.dumps(
                selected_module_structures, indent = 2)

            if selected_module_structures["module_structures"]:
                llm_params["messages"][0]["content"].append({
                    "type": "text",
                    "text": selected_module_structures_description
                })

        # finally append user prompt
        llm_params["messages"][0]["content"].append({
            "type": "text",
            "text": prompt
        })

        anthropic_client = anthropic.Anthropic(api_key = skel['anthropic_api_key'])
        message = anthropic_client.messages.create(**llm_params)
        return message

    @exposed
    @access("user-view")
    def translate(self,
                  text:str,
                  language:str,
                  simplified:bool = False
                  ):
        if not openai:
            raise errors.BadGateway("Needed Dependencies are missing.")

        skel = self.viewSkel()
        key = db.Key(skel.kindName, self.getKey())

        if not skel.read(key):
            raise errors.NotFound()
        logging.error(skel['openai_api_key'])
        openai.api_key = skel['openai_api_key']

        language_options = {
            "en": "english",
            "fr": "french",
            "de": "german",
            "nl": "dutch",
        }

        simplified_language_suffixes = [
            "simplified",
            "short sentences",
            "one information per sentence",
            "simple words",
            "avoid negative language",
            "sentences should be active, not passive",
            "avoid subjunctive clause",
            "one sentence per line",
            "split compound nouns with hyphens"
        ]

        lang_param = language_options[language]
        if simplified:
            lang_param = f"""{lang_param} ({'. '.join(simplified_language_suffixes)})"""

        response = openai.chat.completions.create(
            model = skel['openai_model'],
            messages = [
                {
                    "role"   : "user",
                    "content": f"Translate the following text into {lang_param} and only return the translation, keep Htmltags: {text}\n"
                }
            ],
            n = 1,
            stop = None,
        )
        return response.choices[0].message.content

    @exposed
    @access("user-view")
    def describe_image(self,
                       filekey:str,
                       prompt:str = "", 
                       context:str = "",
                       language:str = "de"):
        
        

        language_options = {
            "en": "english",
            "fr": "french",
            "de": "german",
            "nl": "dutch",
        }
        lang_param = language_options[language]

        def get_resized_image_bytes(image, target_pixel_count = 100_000,
                                    jpeg_quality = 50):
            # assert 0 <= jpeg_quality <= 100, "jpeg_quality must be between 0 and 100"
            if isinstance(image, bytes):
                image = io.BytesIO(image)

            if not isinstance(image, (io.TextIOBase, io.BufferedIOBase, io.RawIOBase, io.IOBase)):
                raise ValueError("image must be file-like or bytes")
            pillow_image = PIL.Image.open(image)
            if pillow_image.format in ['PNG', 'SVG', 'WEBP']:
                jpeg_image = io.BytesIO()
                pillow_image.convert('RGB').save(jpeg_image, 'JPEG')
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
            resized_img.save(result_bio, "jpeg", quality = jpeg_quality)
            result_bio.seek(0)
            return result_bio.read()

        if not openai:
            raise errors.BadGateway("Needed Dependencies are missing.")

        skel = self.viewSkel()
        key = db.Key(skel.kindName, self.getKey())

        if not skel.read(key):
            raise errors.NotFound()

        openai.api_key = skel['openai_api_key']

        blob, mime = conf.main_app.vi.file.read(key=filekey)

        if not blob:
            raise errors.NotFound()
        resized_image_bytes = get_resized_image_bytes(blob)
        base64_image = base64.b64encode(resized_image_bytes).decode("utf-8")
        prompt = f"use the following json data as additional information to describe the image: {re.sub(r'[^a-zA-Z0-9 _-]', '', context)}\n\n" + prompt
        content = [
                        {
                            "type": "text",
                            "text": prompt+ f"\n\nPlease analyze each image and use all provided and generate appropriate HTML alt attributes in {lang_param}, providing only the plain text for the alt attributes."
                         },
                        {
                            "type"     : "image_url",
                            "image_url": {
                                "url"   : f"data:image/jpeg;base64,{base64_image}",
                                # "url": "http://some-domain.com/image.jpeg",
                                "detail": "low",
                                # "low" = 85 Tokens, "high" = calulated differently
                                # "low" = resize (on openapis side) to < 512x512px
                                # https://platform.openai.com/docs/guides/images?api-mode=chat#calculating-costs
                            },
                        },
                    ]
        try:
            completion = openai.chat.completions.create(
                model = skel['openai_model'],
                messages = [
                    {
                        "role"   : "user",
                        "content": content,
                    }
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            logging.error(e)
            raise errors.PreconditionFailed(e.code)


Assistant.json=True