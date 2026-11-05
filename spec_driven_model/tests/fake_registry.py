# Copyright 2026 KMEE
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Load test model classes into the registry and restore it afterwards.

Odoo 19 builds the registry with odoo.orm.model_classes.add_to_registry and
the odoo-test-helper FakeModelLoader no longer works with it, so the tests use
the native API, as the OCA migration guide recommends.
"""

from unittest import mock

from odoo import models
from odoo.orm import model_classes
from odoo.tools import OrderedSet

from ..models.spec_models import SPEC_MIXIN_MAPPINGS


class FakePackage:
    """Stands for a module node in Registry.load."""

    def __init__(self, name):
        self.name = name


class FakeRegistryLoader:
    def __init__(self, env, module_name):
        self.env = env
        self.module_name = module_name

    def backup_registry(self):
        registry = self.env.registry
        self._models = {
            name: {
                "bases": model_cls._base_classes__,
                "inherit": model_cls.__dict__.get("_inherit"),
                "inherit_module": dict(model_cls._inherit_module),
                "inherit_children": list(model_cls._inherit_children),
                "inherits_children": set(model_cls._inherits_children),
            }
            for name, model_cls in registry.models.items()
        }
        self._module_to_models = {
            key: list(value)
            for key, value in models.MetaModel._module_to_models__.items()
        }
        self._mappings = dict(SPEC_MIXIN_MAPPINGS[registry.db_name])
        self._registry_attrs = set(vars(registry))

    def update_registry(self, model_defs):
        """Add the model definitions to the registry, like Registry.load does
        for the classes of a module, then set up and reflect the models."""
        registry = self.env.registry
        cr = self.env.cr
        self.env.flush_all()
        module_models = models.MetaModel._module_to_models__[self.module_name]
        names = []
        for model_def in model_defs:
            if model_def not in module_models:
                module_models.append(model_def)
            # looked up at call time: spec_driven_model wraps it
            name = model_classes.add_to_registry(registry, model_def)._name
            if name not in names:
                names.append(name)
        with mock.patch.object(cr, "commit"):
            registry._setup_models__(cr, names)
            registry.init_models(
                cr, names, {"module": self.module_name, "models_to_check": True}
            )
        return names

    def restore_registry(self):
        registry = self.env.registry
        # nothing may stay pending on the models about to be removed
        self.env.flush_all()
        self.env.invalidate_all()
        for name in list(registry.models):
            if name not in self._models:
                del registry.models[name]
        for name, saved in self._models.items():
            model_cls = registry.models[name]
            model_cls._base_classes__ = saved["bases"]
            if saved["inherit"] is not None:
                model_cls._inherit = saved["inherit"]
            elif "_inherit" in model_cls.__dict__:
                delattr(model_cls, "_inherit")
            model_cls._inherit_module = saved["inherit_module"]
            model_cls._inherit_children = OrderedSet(saved["inherit_children"])
            model_cls._inherits_children = saved["inherits_children"]
            model_cls._setup_done__ = False
        for name in self._models:
            model_classes._init_model_class_attributes(registry.models[name])
        models.MetaModel._module_to_models__.clear()
        models.MetaModel._module_to_models__.update(self._module_to_models)
        SPEC_MIXIN_MAPPINGS[registry.db_name].clear()
        SPEC_MIXIN_MAPPINGS[registry.db_name].update(self._mappings)
        for attr in set(vars(registry)) - self._registry_attrs:
            if attr.endswith("_register_hook_loaded"):
                delattr(registry, attr)
        with mock.patch.object(self.env.cr, "commit"):
            registry._setup_models__(self.env.cr)
