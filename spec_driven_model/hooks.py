# Copyright (C) 2019-TODAY - Raphaël Valyi Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import inspect
import logging
import sys

from odoo import SUPERUSER_ID, api, models

from .models.spec_models import SpecModel, StackedModel

_logger = logging.getLogger(__name__)


def get_remaining_spec_models(cr, registry, module_name, spec_module):
    """
    Figure out the list of spec models not injected into existing
    Odoo models.
    """
    cr.execute(
        """select ir_model.model from ir_model_data
               join ir_model on res_id=ir_model.id
               where ir_model_data.model='ir.model'
               and module=%s;""",
        (module_name,),
    )
    module_models = [
        i[0]
        for i in cr.fetchall()
        if registry.get(i[0]) and not registry[i[0]]._abstract
    ]

    injected_models = set()
    for model in module_models:
        base_class = registry[model]
        # 1st classic Odoo classes
        if hasattr(base_class, "_inherit"):
            injected_models.add(base_class._name)
            for cls in base_class.mro():
                if hasattr(cls, "_inherit") and cls._inherit:
                    if isinstance(cls._inherit, list):
                        inherit_list = cls._inherit
                    else:
                        inherit_list = [cls._inherit]
                    for inherit in inherit_list:
                        if inherit.startswith("spec.mixin."):
                            injected_models.add(cls._name)

    # visit_stack will now need the associated spec classes
    injected_classes = set()
    remaining_models = set()

    for m in injected_models:
        c = SpecModel._odoo_name_to_class(m, spec_module)
        if c is not None:
            injected_classes.add(c)

    for model in module_models:
        base_class = registry[model]
        # 2nd StackedModel classes, that we will visit
        if hasattr(base_class, "_stacked"):
            node = SpecModel._odoo_name_to_class(base_class._stacked, spec_module)

            env = api.Environment(cr, SUPERUSER_ID, {})
            for (
                _kind,
                klass,
                _path,
                _field_path,
                _child_concrete,
            ) in base_class._visit_stack(env, node):
                injected_classes.add(klass)

    all_spec_models = {
        c._name
        for name, c in inspect.getmembers(sys.modules[spec_module], inspect.isclass)
        if c._name in registry
    }

    remaining_models = remaining_models.union(
        {i for i in all_spec_models if i not in [c._name for c in injected_classes]}
    )
    return remaining_models


def register_hook(env, module_name, spec_module, force=False):
    """
    Called by Model#_register_hook once all modules are loaded.
    Here we take all spec models that are not injected in existing concrete
    Odoo models and we make them concrete automatically with
    their _auto_init method that will create their SQL DDL structure.
    """
    load_key = f"_{spec_module}_loaded"
    if hasattr(env.registry, load_key) and not force:  # already done for registry
        return
    setattr(env.registry, load_key, True)

    access_data = []
    remaining_models = get_remaining_spec_models(
        env.cr, env.registry, module_name, spec_module
    )
    for name in remaining_models:
        spec_class = StackedModel._odoo_name_to_class(name, spec_module)
        spec_class._module = "fiscal"  # TODO use python_module ?
        fields = env[spec_class._name]._fields.keys()
        rec_name = next(
            filter(
                lambda x: (
                    x.startswith(env[spec_class._name]._field_prefix)
                    and "_choice" not in x
                ),
                fields,
            )
        )
        model_type = type(
            name,
            (SpecModel, spec_class),
            {
                "_name": name,
                "_inherit": spec_class._inherit,
                "_original_module": "fiscal",
                "_odoo_module": module_name,
                "_spec_module": spec_module,
                "_rec_name": rec_name,
                "_module": module_name,
            },
        )
        models.MetaModel.module_to_models[module_name] += [model_type]

        # now we init these models properly
        # a bit like odoo.modules.loading#load_module_graph would do.
        model = model_type._build_model(env.registry, env.cr)

        env[name]._prepare_setup()
        env[name]._setup_base()
        env[name]._setup_fields()
        env[name]._setup_complete()
        model._auto_fill_access_data(env, module_name, access_data)

    env["ir.model.access"].load(
        [
            "id",
            "name",
            "model_id/id",
            "group_id/id",
            "perm_read",
            "perm_write",
            "perm_create",
            "perm_unlink",
        ],
        access_data,
    )
    hook_key = f"_{module_name}_need_hook"
    if hasattr(env.registry, hook_key) and getattr(env.registry, hook_key):
        env.registry.init_models(env.cr, remaining_models, {"module": module_name})
        setattr(env.registry, hook_key, False)
