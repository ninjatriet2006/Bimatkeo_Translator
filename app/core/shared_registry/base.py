"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.base
- RESPONSIBILITY: The core base class for all factories, composing mixins.
- CALLED BY: app.core.shared_registry.implementations
- CALLS TO: None
- IN = OUT: Provides a unified BaseFactory with registry, metadata, and builder capabilities.
=============================================================================
"""
from typing import Type
from .registry import RegistryMixin
from .metadata import MetadataMixin
from .builder import BuilderMixin

class BaseFactory(RegistryMixin, MetadataMixin, BuilderMixin):
    """
    Base Factory pattern for dynamic plugin management.
    Composes features from mixins.
    """
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Inherited from RegistryMixin but accessed here for registration tracking
        if not hasattr(BaseFactory, '_all_factories'):
            BaseFactory._all_factories = []
        BaseFactory._all_factories.append(cls)
