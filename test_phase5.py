import json
from app.core.factories import TranslatorFactory
import app.plugins.translator.api_translator_impl
import app.plugins.translator.offline_translator_impl

print("1. Testing OpenAI API config loading...")
config_json = json.dumps({
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "model": "gpt-3.5-turbo",
    "key": "test_key",
    "glossary_path": ""
})

try:
    # Use standard registration name from api_translator_impl.py
    translator = TranslatorFactory.create("openai")
    translator.load_weights(config_json)
    
    print(f"OpenAI Translator Created.")
    print(f"Endpoint: {translator.endpoint}")
    print(f"Model: {translator.model}")
    print(f"Key: {translator.key}")
    print(f"Base Prompt Template Length: {len(translator.prompt_builder.base_prompt)}")
    print("SUCCESS: API Translator initialization works.\n")
except Exception as e:
    print(f"FAIL: {e}")

print("2. Testing Offline M2M100 Initialization (Dummy)...")
try:
    offline = TranslatorFactory.create("m2m100")
    print("M2M100 Translator Instantiated Successfully (Waiting for weights).")
except Exception as e:
    print(f"FAIL: {e}")

print("3. Testing DeepSeek Inheritance...")
try:
    deepseek = TranslatorFactory.create("deepseek")
    print(f"DeepSeek Translator Instantiated: {type(deepseek).__name__}")
except Exception as e:
    print(f"FAIL: {e}")

