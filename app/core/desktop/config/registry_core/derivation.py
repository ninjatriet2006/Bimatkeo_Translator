from app.core.shared_registry import TranslatorFactory
from app.core.desktop.constants import CAT_OTHER_ACTIONS

class RegistryDerivation:
    def __init__(self, registry_mixin):
        self.rm = registry_mixin

    def derive_all(self):
        self.derive_default_checks()
        self.derive_capabilities_and_groups()
        self.derive_sources()
        self.derive_labels()

    def derive_default_checks(self):
        checks = {}
        for field, by_key in getattr(self.rm, 'model_registry', {}).items():
            field_checks = {}
            for key, entry in by_key.items():
                rule = {}
                if "check_file" in entry:
                    rule["check_file"] = entry["check_file"]
                if "check_module" in entry:
                    rule["check_module"] = entry["check_module"]
                field_checks[key] = rule
            checks[field] = field_checks
        self.rm._DEFAULT_CHECKS = checks
        self.rm._model_checks = {field: dict(rules) for field, rules in checks.items()}

    def derive_capabilities_and_groups(self):
        groups = {}
        capabilities = {}
        for field, group_name in self.rm.GROUP_NAMES.items():
            by_key = getattr(self.rm, 'model_registry', {}).get(field, {})
            groups[group_name] = list(by_key.keys())
            for key in by_key.keys():
                caps = TranslatorFactory.get_capabilities(key)
                capabilities[key] = caps
        groups[CAT_OTHER_ACTIONS] = ["original", "none"]
        capabilities["original"] = {}
        capabilities["none"] = {}
        self.rm.registry_translator_groups = groups
        self.rm.registry_translator_capabilities = capabilities

    def derive_sources(self):
        sources = {}
        for field, by_key in getattr(self.rm, 'model_registry', {}).items():
            for key, entry in by_key.items():
                if entry.get("source"):
                    sources[key] = entry["source"]
        self.rm.model_source_map = sources

    def derive_labels(self):
        labels = {}
        for field, by_key in getattr(self.rm, 'model_registry', {}).items():
            field_labels = {}
            for key, entry in by_key.items():
                field_labels[key] = entry.get("label") or key
            labels[field] = field_labels
        self.rm.model_labels = labels
