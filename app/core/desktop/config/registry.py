import os
from typing import TYPE_CHECKING
from app.core.desktop.constants import CAT_OFFLINE_MODELS, CAT_API_BASED, CAT_OTHER_ACTIONS
from app.core.shared_registry.core.loader import RegistryLoader
from app.core.shared_registry.core.derivation import RegistryDerivation
from app.core.shared_registry.core.utils import RegistryUtils
from app.core.shared_registry.core.hardware import RegistryHardware

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
    REGISTRY_RELATIVE_PATH = os.path.join(".config", "models", "model_registry.yaml")

    GROUP_NAMES = {
        "offline_translator": CAT_OFFLINE_MODELS,
        "ai_translator": CAT_API_BASED,
    }

    @property
    def registry_loader(self):
        if not hasattr(self, '_registry_loader'):
            self._registry_loader = RegistryLoader(self)
        return self._registry_loader

    @property
    def registry_derivation(self):
        if not hasattr(self, '_registry_derivation'):
            self._registry_derivation = RegistryDerivation(self)
        return self._registry_derivation

    @property
    def registry_utils(self):
        if not hasattr(self, '_registry_utils'):
            self._registry_utils = RegistryUtils(self)
        return self._registry_utils

    @property
    def registry_hardware(self):
        if not hasattr(self, '_registry_hardware'):
            self._registry_hardware = RegistryHardware(self)
        return self._registry_hardware

    def _registry_path(self):
        return self.registry_loader.registry_path()

    def _resolve_os_placeholders(self, path):
        return self.registry_loader.resolve_os_placeholders(path)

    def load_registry(self):
        return self.registry_loader.load_registry()

    def _validate_fields(self, fields):
        return self.registry_loader.validate_fields(fields)

    def _derive_all(self):
        return self.registry_derivation.derive_all()

    def _derive_default_checks(self):
        return self.registry_derivation.derive_default_checks()

    def _derive_capabilities_and_groups(self):
        return self.registry_derivation.derive_capabilities_and_groups()

    def _derive_sources(self):
        return self.registry_derivation.derive_sources()

    def _derive_labels(self):
        return self.registry_derivation.derive_labels()

    def format_display_label(self, key, field=None):
        return self.registry_utils.format_display_label(key, field)

    def list_field_keys(self, field):
        return self.registry_utils.list_field_keys(field)

    def resolve_available_model(self, field, current_value):
        return self.registry_utils.resolve_available_model(field, current_value)

    def sweep_settings(self, settings):
        return self.registry_utils.sweep_settings(settings)

    def missing_required_fields(self, settings):
        return self.registry_utils.missing_required_fields(settings)

    def _machine_fingerprint(self):
        return self.registry_hardware.machine_fingerprint()

    def optimize_profiles_once(self):
        return self.registry_hardware.optimize_profiles_once()
