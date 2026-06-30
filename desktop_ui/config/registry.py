import os
import sys
import random
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
from desktop_ui.constants import *


_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")
_exe_ext = ".exe" if _os_suffix == "win" else ""


from typing import TYPE_CHECKING
from app.core.factories import TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory, UpscalerFactory, ColorizerFactory, RendererFactory, CloudOCRFactory

FACTORY_MAP = {
    "offline_translator": TranslatorFactory,
    "ai_translator": TranslatorFactory,
    "offline_detector": DetectorFactory,
    "offline_ocr": RecognizerFactory,
    "api_ocr": CloudOCRFactory,
    "inpainter": InpainterFactory,
    "upscaler": UpscalerFactory,
    "colorizer": ColorizerFactory,
    "renderer": RendererFactory,
}

if TYPE_CHECKING:
    class _RegistryMixinBase:
        project_base_dir: str
        all_model_fields: list[str]
        required_model_fields: list[str]
        def check_model_existence(self, model_name: str, field: str | None = None) -> bool: ...
        def save_oldsession_config(self) -> None: ...
else:
    _RegistryMixinBase = object

class RegistryMixin(_RegistryMixinBase):
    """Single source of truth loader for all model metadata.

    Reads .config/models/model_registry.yaml and derives every structure the
    rest of the app needs (_DEFAULT_CHECKS, TRANSLATOR_GROUPS,
    TRANSLATOR_CAPABILITIES, model sources, display labels). If the file is
    missing or corrupt, a minimal seed is written so the app self-heals.
    """
    
    project_base_dir: str

    REGISTRY_RELATIVE_PATH = os.path.join(".config", "models", "model_registry.yaml")

    # Minimal seed used ONLY when the registry file is missing/unreadable.
    _SEED_REGISTRY = {
        "schema_version": 1,
        "required_fields": ["offline_detector", "offline_ocr", "inpainter"],
        "fields": {
            "offline_translator": [
                {"key": "m2m100", "check_file": "models/Offline Translator/M2M100/sentencepiece.model"},
                {"key": "offline", "check_file": "models/Offline Translator/M2M100/sentencepiece.model"},
            ],
            "ai_translator": [
                {"key": "gemini", "check_file": "app/translators/gemini.py", "check_module": "google.genai"},
            ],
            "offline_ocr": [
                {"key": "mocr", "check_file": "app/ocr/mocr.py", "check_module": "manga_ocr"},
            ],
            "offline_detector": [
                {"key": "default", "check_file": "models/Detector/CTD/detect-20241225.ckpt"},
                {"key": "none"},
            ],
            "inpainter": [
                {"key": "opencv", "check_file": "none"},
                {"key": "default", "check_file": "models/Inpainter/Lama_Large/lama_large_512px.ckpt"},
                {"key": "manga", "check_file": "models/Inpainter/Manga_ONNX/erika.onnx"},
                {"key": "none"},
            ],
            "diffusion_model": [
                {"key": "none"},
            ],
            "upscaler": [
                {"key": "waifu2x", "check_file": "models/Upscaler/Waifu2x/waifu2x-{os}/waifu2x-ncnn-vulkan{exe}"},
            ],
            "colorizer": [
                {"key": "none"},
            ],
        },
    }

    GROUP_NAMES = {
        "offline_translator": CAT_OFFLINE_MODELS,
        "ai_translator": CAT_API_BASED,
    }

    # ------------------------------------------------------------------ load
    def _registry_path(self):
        return os.path.join(self.project_base_dir, self.REGISTRY_RELATIVE_PATH)

    def _resolve_os_placeholders(self, path):
        if not isinstance(path, str):
            return path
        return path.replace("{os}", _os_suffix).replace("{exe}", _exe_ext)

    def load_registry(self):
        """Loads and validates the registry. Stores derived structures on self.

        Sets:
            self.model_registry      -> {field: {key: entry_dict}}
            self.model_labels        -> {field: {key: label}}
            self.model_source_map    -> {key: source_url}
        Never raises: on any failure it falls back to the seed.
        """
        path = self._registry_path()
        raw = None
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = yaml.load(f)
            except Exception as e:
                print(f"[Registry] Failed to parse model_registry.yaml: {e}. Using seed.")
                raw = None

        if not isinstance(raw, dict) or not isinstance(raw.get("fields"), dict):
            if raw is not None:
                print("[Registry] model_registry.yaml malformed (missing 'fields'). Using seed.")
            raw = self._SEED_REGISTRY
            self._write_registry(raw)

        import typing
        self.full_registry = raw
        fields = typing.cast(dict, raw.get("fields", {}))
        self.all_model_fields = list(fields.keys())
        self.required_model_fields = typing.cast(list, raw.get("required_fields", []))
        self.global_settings = typing.cast(dict, raw.get("global_settings", {}))

        self.model_registry = self._validate_fields(fields)
        self._derive_all()
        return self.model_registry

    def _write_registry(self, data):
        path = self._registry_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f)
            print("[Registry] Wrote seed model_registry.yaml (self-heal).")
        except Exception as e:
            print(f"[Registry] Could not write seed registry: {e}")

    def _validate_fields(self, fields):
        """Validates each block. Bad blocks are skipped with a warning, never crash."""
        validated = {}
        for field, entries in fields.items():
            if not isinstance(entries, list):
                print(f"[Registry] Field '{field}' is not a list. Skipping field.")
                continue
            by_key = {}
            for idx, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    print(f"[Registry] {field}[{idx}] is not a mapping. Skipping block.")
                    continue
                key = entry.get("key")
                if not key or not isinstance(key, str):
                    print(f"[Registry] {field}[{idx}] missing valid 'key'. Skipping block.")
                    continue
                if key in by_key:
                    print(f"[Registry] Duplicate key '{key}' in '{field}'. Keeping first, skipping duplicate.")
                    continue
                clean = dict(entry)
                if "check_file" in clean:
                    clean["check_file"] = self._resolve_os_placeholders(clean["check_file"])
                by_key[key] = clean
            validated[field] = by_key
        return validated

    # ----------------------------------------------------------------- derive
    def _derive_all(self):
        self._derive_default_checks()
        self._derive_capabilities_and_groups()
        self._derive_sources()
        self._derive_labels()

    def _derive_default_checks(self):
        checks = {}
        for field, by_key in self.model_registry.items():
            field_checks = {}
            for key, entry in by_key.items():
                rule = {}
                if "check_file" in entry:
                    rule["check_file"] = entry["check_file"]
                if "check_module" in entry:
                    rule["check_module"] = entry["check_module"]
                field_checks[key] = rule
            checks[field] = field_checks
        self._DEFAULT_CHECKS = checks
        # check_model_existence prioritizes _model_checks over _DEFAULT_CHECKS,
        # so mirror the registry there too. This makes the registry the single
        # source for BOTH lookup paths and prevents stale legacy YAML entries
        # (loaded later by register_model_checks) from shadowing the registry.
        self._model_checks = {field: dict(rules) for field, rules in checks.items()}

    def _derive_capabilities_and_groups(self):
        groups = {}
        capabilities = {}
        for field, group_name in self.GROUP_NAMES.items():
            by_key = self.model_registry.get(field, {})
            groups[group_name] = list(by_key.keys())
            for key in by_key.keys():
                caps = TranslatorFactory.get_capabilities(key)
                capabilities[key] = caps
        groups[CAT_OTHER_ACTIONS] = ["original", "none"]
        capabilities["original"] = {}
        capabilities["none"] = {}
        self.registry_translator_groups = groups
        self.registry_translator_capabilities = capabilities

    def _derive_sources(self):
        sources = {}
        for field, by_key in self.model_registry.items():
            for key, entry in by_key.items():
                if entry.get("source"):
                    sources[key] = entry["source"]
        self.model_source_map = sources

    def _derive_labels(self):
        labels = {}
        for field, by_key in self.model_registry.items():
            field_labels = {}
            for key, entry in by_key.items():
                field_labels[key] = entry.get("label") or key
            labels[field] = field_labels
        self.model_labels = labels

    # --------------------------------------------------------------- helpers
    def format_display_label(self, key, field=None):
        """Returns the display label for a model key (falls back to the key)."""
        if not isinstance(key, str):
            return str(key)
        
        if key == "none":
            return "--- Not Used ---"
        if key == "original":
            return "--- Original ---"
            
        # 1. Query the dynamic factory for DISPLAY_NAME if field is provided
        if field and field in FACTORY_MAP:
            factory = FACTORY_MAP[field]
            display = factory.get_display_name(key)
            if display != key:
                return display
                
        # 2. Query ALL factories if field is not provided
        if not field:
            for factory in FACTORY_MAP.values():
                display = factory.get_display_name(key)
                if display != key:
                    return display
                    
        # 3. Fallback to YAML (legacy support)
        labels = getattr(self, "model_labels", {})
        if field and field in labels and key in labels[field]:
            return labels[field][key]
        for field_labels in labels.values():
            if key in field_labels:
                return field_labels[key]
                
        return key

    def list_field_keys(self, field):
        return list(getattr(self, "model_registry", {}).get(field, {}).keys())

    def resolve_available_model(self, field, current_value):
        """Returns current_value if it still exists in the registry; otherwise a
        fallback replacement.

        IMPORTANT (Plan A): fallback fires ONLY when current_value was genuinely
        DELETED from the registry. A model that is present in the registry but
        not yet downloaded is KEPT as-is (it simply shows '(Not Setup)' in the
        UI). This makes the sweep non-destructive on fresh machines where no
        model files have been downloaded.

        Replacement preference when the current model is deleted:
          1. a random model that is present AND already set up (ready to use)
          2. else a random model that is present in the registry (any)
          3. else '' (no models defined for this field)
        """
        registry = getattr(self, "model_registry", {})
        by_key = registry.get(field, {})

        # Still defined in the registry -> keep it untouched (Plan A).
        if current_value and current_value in by_key:
            return current_value

        def is_setup(key):
            try:
                return self.check_model_existence(key, field=field)
            except Exception:
                return False

        ready = [k for k in by_key.keys() if is_setup(k)]
        if ready:
            return random.choice(ready)
        if by_key:
            return random.choice(list(by_key.keys()))
        return ""

    # Maps a settings-dict key to the registry field used to validate it.
    # 'translator' is resolved specially (offline OR ai) by sweep_settings.
    SETTINGS_FIELD_MAP = {
        "offline_translator": "offline_translator",
        "ai_translator": "ai_translator",
        "offline_detector": "offline_detector",
        "offline_ocr": "offline_ocr",
        "api_ocr": "api_ocr",
        "inpainter": "inpainter",
        "upscaler": "upscaler",
        "colorizer": "colorizer",
    }

    def sweep_settings(self, settings):
        """Repairs every model field in a settings dict in place.

        For each model-bearing key, if its value points at a model that is no
        longer available (deleted from the registry or not set up), it is
        replaced via resolve_available_model (random available, or '' if none).

        The 'translator' key is resolved against whichever category applies:
        offline_translator or ai_translator.

        Returns a list of (key, old_value, new_value) tuples describing changes.
        """
        if not isinstance(settings, dict):
            return []

        changes = []

        for key, field in self.SETTINGS_FIELD_MAP.items():
            if key not in settings:
                continue
            old = settings.get(key)
            if old in (None, "", "none", "original"):
                continue
            new = self.resolve_available_model(field, old)
            if new != old:
                settings[key] = new
                changes.append((key, old, new))

        # The backend 'translator' value depends on the selected category. Keep
        # it in sync with the corresponding category key so the two never
        # disagree after a fallback.
        category = settings.get("translator_category", "Offline")
        is_ai = category not in ("Offline", None, "")
        category_key = "ai_translator" if is_ai else "offline_translator"
        field = category_key

        if "translator" in settings:
            old = settings.get("translator")
            if old not in (None, "", "none", "original"):
                # Prefer mirroring the already-resolved category key so both stay
                # consistent; fall back to resolving 'translator' on its own.
                if category_key in settings and settings[category_key] not in (None, "", "none", "original"):
                    new = settings[category_key]
                else:
                    new = self.resolve_available_model(field, old)
                if new != old:
                    settings["translator"] = new
                    changes.append(("translator", old, new))

        return changes

    def missing_required_fields(self, settings):
        """Returns the list of REQUIRED fields whose value is blank/unavailable.

        Used to block a job from running when a mandatory model (detector, ocr,
        inpainter) has no usable value after fallback.
        """
        if not isinstance(settings, dict):
            return []
        missing = []
        for field in self.required_model_fields:
            value = settings.get(field)
            if value in (None, "", "none"):
                missing.append(field)
                continue
            try:
                if not self.check_model_existence(value, field=field):
                    missing.append(field)
            except Exception:
                missing.append(field)
        return missing

    # ------------------------------------------------------------- optimize
    def _machine_fingerprint(self):
        """Stable per-machine id used to run the optimize sweep once per machine."""
        import platform
        try:
            return f"{platform.node()}|{platform.machine()}|{_os_suffix}"
        except Exception:
            return _os_suffix

    def optimize_profiles_once(self):
        """Runs the model fallback sweep across stored profiles/config ONCE per machine.

        Sweeps every preset profile in profiles.yaml and the default settings in
        studio_config (if present), repairing any model field that points at a
        deleted or not-set-up model. Records the machine fingerprint in
        studio_config so it does not run again on the same machine.

        Safe to call on every startup: it is a no-op after the first successful run.
        Never raises.
        """
        try:
            studio = getattr(self, "studio_config", None)
            oldsession = getattr(self, "oldsession_config", None)
            if not isinstance(oldsession, dict):
                return

            fingerprint = self._machine_fingerprint()
            if oldsession.get("registry_optimized_for") == fingerprint:
                return

            total_changes = []

            # 1. Sweep preset profiles.yaml
            profiles_path = os.path.join(
                self.project_base_dir, ".config", "configs", "profiles.yaml"
            )
            if os.path.exists(profiles_path):
                try:
                    with open(profiles_path, "r", encoding="utf-8") as f:
                        profiles = yaml.load(f) or {}
                    if isinstance(profiles, dict):
                        dirty = False
                        for name, settings in profiles.items():
                            changes = self.sweep_settings(settings)
                            if changes:
                                dirty = True
                                total_changes.extend((name, k, o, n) for (k, o, n) in changes)
                        if dirty:
                            with open(profiles_path, "w", encoding="utf-8") as f:
                                yaml.dump(profiles, f)
                except Exception as e:
                    print(f"[Registry] optimize: failed sweeping profiles.yaml: {e}")

            # 2. Sweep default settings embedded in studio_config, if any.
            if isinstance(studio, dict):
                default_settings = studio.get("default_settings")
                if isinstance(default_settings, dict):
                    changes = self.sweep_settings(default_settings)
                    if changes:
                        total_changes.extend(("<defaults>", k, o, n) for (k, o, n) in changes)

            oldsession["registry_optimized_for"] = fingerprint
            try:
                self.save_oldsession_config()
            except Exception as e:
                print(f"[Registry] optimize: could not persist oldsession_config: {e}")

            if total_changes:
                print(f"[Registry] optimize: repaired {len(total_changes)} model field(s):")
                for entry in total_changes:
                    print(f"           {entry[0]}: {entry[1]} -> {entry[2]} ({entry[3] if len(entry) > 3 else ''})")
            else:
                print("[Registry] optimize: all model fields valid for this machine.")
        except Exception as e:
            print(f"[Registry] optimize_profiles_once failed (non-fatal): {e}")
