# Copyright (C) 2019 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import sys
import inspect
from odoo import api, models, SUPERUSER_ID
from .models.spec_models import SpecModel, StackedModel


def post_init_hook(cr, registry, module_name, spec_module):
    "automatically generate access rules for spec models"
    env = api.Environment(cr, SUPERUSER_ID, {})
    # TODO no hardcode
    remaining_models = get_remaining_spec_models(
        cr, registry, module_name, spec_module)
    fields = ['id', 'name', 'model_id/id', 'group_id/id',
              'perm_read', 'perm_write' , 'perm_create', 'perm_unlink']
    access_data = []
    for model in remaining_models:
        underline_name = model.replace('.', '_')
        rec_id = "acl_%s_nfe_40_%s" % ('todo'.split('.')[-1],
                                     underline_name)
        # TODO no nfe ref
        model_id = "l10n_br_nfe_spec.model_%s" % (underline_name,)
        access_data.append([rec_id, underline_name, model_id, 'base.group_user',
                            '1', '1', '1', '1'])
        # TODO make more secure!
    env['ir.model.access'].load(fields, access_data)

def get_remaining_spec_models(cr, registry, module_name, spec_module):
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
    remaining_models = set(['nfe.40.tveiculo'])  # TODO
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

            # TODO with registry!!
            base_class._visit_stack(node, injected_classes,
                                   base_class._stacked.split('.')[-1],
                                   registry, cr)
            # for f in base_class._stack_skip:
            #    if base_class._fields[]

    used_models = [c._name for c in injected_classes]
    print(" **** injected spec models (%s): %s" % (
        len(used_models), used_models))
    # TODO replace by SELECT like for module_models ?
    all_spec_models = set([c._name for name, c
                           in inspect.getmembers(
                               sys.modules[spec_module], inspect.isclass)])

    print("number of all spec models:", len(all_spec_models))
    remaining_models = remaining_models.union(
        set([i for i in all_spec_models
             if i not in [c._name for c in injected_classes]]))
    print("\n **** REMAINING spec models to init (%s): %s \n\n" % (
        len(remaining_models), remaining_models))
    return remaining_models

def register_hook(env, module_name, spec_module):
    remaining_models = get_remaining_spec_models(env.cr, env.registry,
                                                 module_name, spec_module)
    for name in remaining_models:
        spec_class = StackedModel._odoo_name_to_class(name, spec_module)
        spec_class._module = "fiscal"  # TODO use python_module ?
        c = type(name, (SpecModel, spec_class),
                 {'_name': spec_class._name,
                  '_inherit': ['spec.mixin.nfe'],
                  '_original_module': "fiscal",
                  '_rec_name': spec_class._concrete_rec_name})
        models.MetaModel.module_to_models[module_name] += [c]

        # now we init these models properly
        # a bit like odoo.modules.loading#load_module_graph would do.
        c._build_model(env.registry, env.cr)

        env[name]._prepare_setup()
        env[name]._setup_base()
        env[name]._setup_fields()
        env[name]._setup_complete()

    # TODO only in update mode!
    env.registry.init_models(env.cr, remaining_models, {'module': module_name})
