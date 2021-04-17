# Copyright (C) 2019-TODAY - Raphaël Valyi Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import sys
import inspect
from odoo import api, models, SUPERUSER_ID
from .models.spec_models import SpecModel, StackedModel

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry, module_name, spec_module):
    """
    Automatically generate access rules for spec models
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    remaining_models = get_remaining_spec_models(
        cr, registry, module_name, spec_module)
    fields = ['id', 'name', 'model_id/id', 'group_id/id',
              'perm_read', 'perm_write', 'perm_create', 'perm_unlink']
    access_data = []
    for model in remaining_models:
        underline_name = model.replace('.', '_')
        model_id = "%s_spec.model_%s" % (module_name, underline_name,)
        access_data.append(["access_%s_user" % (underline_name,),
                            underline_name, model_id,
                            '%s.group_user' % (module_name,),
                            '1', '0', '0', '0'])
        access_data.append(["access_%s_manager" % (underline_name,),
                            underline_name, model_id,
                            '%s.group_manager' % (module_name,),
                            '1', '1', '1', '1'])
    env['ir.model.access'].load(fields, access_data)


def get_remaining_spec_models(cr, registry, module_name, spec_module):
    """
    Figure out the list of spec models not injected into existing
    Odoo models.
    """
    cr.execute("""select ir_model.model from ir_model_data
               join ir_model on res_id=ir_model.id
               where ir_model_data.model='ir.model'
               and module=%s;""", (module_name,))
    module_models = [i[0] for i in cr.fetchall() if registry.get(i[0])
                     and not registry[i[0]]._abstract]

    injected_models = set()
    for model in module_models:
        base_class = registry[model]
        # 1st classic Odoo classes
        if hasattr(base_class, '_inherit'):
            injected_models.add(base_class._name)
            if isinstance(base_class._inherit, list):
                injected_models = injected_models.union(
                    set(base_class._inherit))
            elif base_class._inherit is not None:
                injected_models.add(base_class._inherit)

    # visit_stack will now need the associated spec classes
    injected_classes = set()
    remaining_models = set()
    # TODO when using a registry loading, use _stack_skip to find
    # out which models to leave concrete, see later commented loop

    for m in injected_models:
        c = SpecModel._odoo_name_to_class(m, spec_module)
        if c is not None:
            injected_classes.add(c)

    for model in module_models:
        base_class = registry[model]
        # 2nd StackedModel classes, that we will visit
        if hasattr(base_class, '_stacked'):
            node = SpecModel._odoo_name_to_class(base_class._stacked,
                                                 spec_module)

            base_class._visit_stack(node, injected_classes,
                                    base_class._stacked.split('.')[-1],
                                    registry, cr)

    all_spec_models = set([c._name for name, c
                           in inspect.getmembers(
                               sys.modules[spec_module], inspect.isclass)])

    remaining_models = remaining_models.union(
        set([i for i in all_spec_models
             if i not in [c._name for c in injected_classes]]))
    return remaining_models


def register_hook(env, module_name, spec_module):
    """
    Called by Model#_register_hook once all modules are loaded.
    Here we take all spec models that not injected in existing concrete
    Odoo models and we make them concrete automatically with
    their _auto_init method that will create their SQL DDL structure.
    """
    remaining_models = get_remaining_spec_models(env.cr, env.registry,
                                                 module_name, spec_module)
    for name in remaining_models:
        spec_class = StackedModel._odoo_name_to_class(name, spec_module)
        spec_class._module = "fiscal"  # TODO use python_module ?
        c = type(name, (SpecModel, spec_class),
                 {'_name': spec_class._name,
                  '_inherit': [spec_class._inherit, 'spec.mixin'],
                  '_original_module': "fiscal",
                  '_odoo_module': module_name,
                  '_spec_module': spec_module,
                  '_rec_name': spec_class._concrete_rec_name})
        models.MetaModel.module_to_models[module_name] += [c]

        # now we init these models properly
        # a bit like odoo.modules.loading#load_module_graph would do.
        c._build_model(env.registry, env.cr)

        env[name]._prepare_setup()
        env[name]._setup_base()
        env[name]._setup_fields()
        env[name]._setup_complete()

    hook_key = '_%s_need_hook' % (module_name,)
    if hasattr(env.registry, hook_key) and getattr(env.registry, hook_key):
        env.registry.init_models(env.cr, remaining_models,
                                 {'module': module_name})
        setattr(env.registry, hook_key, False)
