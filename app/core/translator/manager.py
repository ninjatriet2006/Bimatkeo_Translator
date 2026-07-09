"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.manager
- RESPONSIBILITY: Initializes and allocates Translator and Editor objects based on config.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.factories (TranslatorFactory)
- IN = OUT: Receives config_dict -> returns instances of Translator and Editor.
=============================================================================
"""

from app.core.factories import TranslatorFactory
from app.core.downloader import ModelDownloader

class TranslatorManager:
    @staticmethod
    def initialize(config_dict: dict, project_root: str, api_profiles: dict, log_callback=None):
        """
        Khởi tạo và trả về (chained_translators, editor_translator) dựa trên config.
        chained_translators là list các tuple (translator_instance, target_lang).
        """
        enable_translator = config_dict.get("pipeline", {}).get("enable_translator", True)
        if not enable_translator:
            return [], None

        translator_dict = config_dict.get("translator", {})
        target_lang = translator_dict.get("target_lang", "VIN")
        enable_translator_chain = translator_dict.get("enable_translator_chain", False)
        translator_chain_str = translator_dict.get("translator_chain", "")
        
        chained_translators = []
        editor_translator = None

        if enable_translator_chain and translator_chain_str:
            steps = [s for s in translator_chain_str.split(';') if s]
            for step in steps:
                if ':' in step:
                    t_name, t_lang = step.split(':', 1)
                    step_translator = None
                    if t_name in api_profiles:
                        prof = api_profiles[t_name]
                        provider_name = prof.get('provider', 'openai')
                        try:
                            step_translator = TranslatorFactory.create(provider_name)
                            step_translator.log_callback = log_callback
                            step_translator.load_weights({
                                "endpoint": prof.get('endpoint'),
                                "model": prof.get('model'),
                                "key": prof.get('key'),
                                "max_retries": prof.get('max_retries', 3),
                                "system_prompt_profile": translator_dict.get("system_prompt_profile", "None"),
                                "project_base_dir": project_root
                            })
                        except Exception as e:
                            if log_callback: log_callback("ERROR", f"Failed to load chain translator '{t_name}': {e}")
                    else:
                        try:
                            step_translator = TranslatorFactory.create(t_name)
                            step_translator.log_callback = log_callback
                            step_translator.load_weights({
                                "system_prompt_profile": translator_dict.get("system_prompt_profile", "None"),
                                "project_base_dir": project_root
                            })
                        except Exception as e:
                            if log_callback: log_callback("ERROR", f"Failed to load chain translator '{t_name}': {e}")
                    
                    if step_translator:
                        chained_translators.append((step_translator, t_lang))
        else:
            # Khởi tạo Translator chính
            translator = None
            try:
                if 'pool_apis' in translator_dict and translator_dict['pool_apis']:
                    api_info = translator_dict['pool_apis'][0]
                    provider_name = api_info.get('translator', 'openai')
                    translator = TranslatorFactory.create(provider_name)
                    translator.log_callback = log_callback
                    translator.load_weights({
                        "endpoint": api_info.get('endpoint'),
                        "model": api_info.get('model'),
                        "key": api_info.get('api_key', api_info.get('key', '')),
                        "max_retries": translator_dict.get('max_retries', 3),
                        "glossary_path": translator_dict.get('glossary_path', ''),
                        "system_prompt_profile": translator_dict.get('system_prompt_profile', 'None'),
                        "project_base_dir": project_root
                    })
                else:
                    provider_name = translator_dict.get('translator', 'openai')
                    translator = TranslatorFactory.create(provider_name)
                    translator.log_callback = log_callback
                    category = translator_dict.get('translator_category', 'Offline')
                    
                    if category == 'Offline' or provider_name in ['nllb', 'm2m100']:
                        try:
                            trans_path = TranslatorFactory.get_model_path_from_registry("offline_translator", provider_name)
                            translator.load_weights(trans_path)
                        except ValueError:
                            if log_callback:
                                log_callback("ERROR", f"Offline translator '{provider_name}' not found.")
                            translator = None
                    else:
                        translator.load_weights({
                            "endpoint": translator_dict.get('ai_endpoint'),
                            "model": translator_dict.get('ai_model'),
                            "key": translator_dict.get('ai_api_key', translator_dict.get('ai_key', '')),
                            "max_retries": translator_dict.get('max_retries', 3),
                            "glossary_path": translator_dict.get('glossary_path', ''),
                            "system_prompt_profile": translator_dict.get('system_prompt_profile', 'None'),
                            "project_base_dir": project_root
                        })
            except Exception as e:
                if log_callback:
                    log_callback("ERROR", f"Failed to load translator: {e}")
                translator = None
                
            if translator:
                chained_translators.append((translator, target_lang))

        # Khởi tạo Editor (Double Check)
        if str(config_dict.get("enable_double_check", "Yes")).lower() in ["yes", "true", "1"]:
            try:
                if 'pool_apis' in translator_dict and translator_dict['pool_apis']:
                    api_info = translator_dict['pool_apis'][0]
                    provider_name = api_info.get('translator', 'openai')
                    editor_translator = TranslatorFactory.create(provider_name)
                    editor_translator.log_callback = log_callback
                    editor_translator.load_weights({
                        "endpoint": api_info.get('endpoint'),
                        "model": api_info.get('model'),
                        "key": api_info.get('api_key', api_info.get('key', '')),
                        "max_retries": translator_dict.get('max_retries', 3),
                        "glossary_path": translator_dict.get('glossary_path', ''),
                        "system_prompt_profile": "editor",
                        "project_base_dir": project_root
                    })
                else:
                    provider_name = translator_dict.get('translator', 'openai')
                    editor_translator = TranslatorFactory.create(provider_name)
                    editor_translator.log_callback = log_callback
                    category = translator_dict.get('translator_category', 'Offline')
                    
                    if category == 'Offline' or provider_name in ['nllb', 'm2m100']:
                        try:
                            trans_path = TranslatorFactory.get_model_path_from_registry("offline_translator", provider_name)
                            editor_translator.load_weights(trans_path)
                        except ValueError:
                            if log_callback:
                                log_callback("ERROR", f"Offline editor translator '{provider_name}' not found.")
                            editor_translator = None
                    else:
                        editor_translator.load_weights({
                            "endpoint": translator_dict.get('ai_endpoint'),
                            "model": translator_dict.get('ai_model'),
                            "key": translator_dict.get('ai_api_key', translator_dict.get('ai_key', '')),
                            "max_retries": translator_dict.get('max_retries', 3),
                            "glossary_path": translator_dict.get('glossary_path', ''),
                            "system_prompt_profile": "editor",
                            "project_base_dir": project_root
                        })
            except Exception as e:
                if log_callback:
                    log_callback("ERROR", f"Failed to load editor translator: {e}")
                editor_translator = None

        return chained_translators, editor_translator
