# Copyright 2019-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import sys
import collections
from inspect import getmembers, isclass
from odoo import api, models, SUPERUSER_ID, _
import logging

_logger = logging.getLogger(__name__)


class SpecModel(models.AbstractModel):
    """When you inherit this Model, then your model becomes concrete just like
    models.Model and it can use _inherit to inherit from several xsd generated
    spec mixins.
    All your model relational fields will be automatically mutated according to
    which concrete models the spec mixins where injected in.
    Because of this field mutation logic in _build_model, SpecModel should be
    inherited the Python way YourModel(spec_models.SpecModel)
    and not through _inherit.
    """
    _inherit = 'spec.mixin'
    _auto = True                # automatically create database backend
    _register = False           # not visible in ORM registry
    _abstract = False
    _transient = False

    # TODO generic onchange method that check spec field simple type formats
    # xsd_required, according to the considered object context
    # and return warning or reformat things
    # ideally the list of onchange fields is set dynamically but if it is too
    # hard, we can just dump the list of fields when SpecModel is loaded

    # TODO a save python constraint that ensuire xsd_required fields for the
    # context are present

    @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    def _compute_display_name(self):
        "More user friendly when automatic _rec_name is bad"
        res = super(SpecModel, self)._compute_display_name()
        for rec in self:
            if rec.display_name == "False" or not rec.display_name:
                rec.display_name = _("Abrir...")
        return res

    @classmethod
    def _build_model(cls, pool, cr):
        """
        xsd generated spec mixins do not need to depend on this opinionated
        module. That's why the spec.mixin is dynamically injected as a parent
        class as long as generated class inherit from some
        spec.mixin.<schema_name> mixin.
        """
        parents = cls._inherit
        parents = [parents] if isinstance(parents, str) else (parents or [])
        for parent in parents:
            super_parents = pool[parent]._inherit
            if isinstance(super_parents, str):
                super_parents = [super_parents]
            else:
                super_parents = super_parents or []
            for super_parent in super_parents:
                if super_parent.startswith('spec.mixin.'):
                    cr.execute(
                        "SELECT name FROM ir_module_module "
                        "WHERE name=%s "
                        "AND state in ('to install', 'to upgrade', 'to remove')",
                        (pool[super_parent]._odoo_module,))
                    if cr.fetchall():
                        setattr(pool, '_%s_need_hook'
                                % (pool[super_parent]._odoo_module,), True)

                    cls._map_concrete(parent, cls._name)
                    if not hasattr(pool[parent], 'build'):  # FIXME BRITTLE
                        pool[parent]._inherit = super_parents + ['spec.mixin']
                        pool[parent].__bases__ = ((pool['spec.mixin'],)
                                                  + pool[parent].__bases__)
        return super(SpecModel, cls)._build_model(pool, cr)

    @api.model
    def _setup_fields(self):
        """
        SpecModel models inherit their fields from XSD generated mixins.
        These mixins can either be made concrete, either be injected into
        existing concrete Odoo models. In that last case, the comodels of the
        relational fields pointing to such mixins should be remapped to the
        proper concrete models where these mixins are injected.
        """
        cls = type(self)
        for klass in cls.__bases__:
            if not hasattr(klass, '_name')\
                    or not hasattr(klass, '_fields')\
                    or klass._name is None\
                    or not klass._name.startswith(self.env[cls._name]._schema_name):
                continue
            if klass._name != cls._name:
                cls._map_concrete(klass._name, cls._name)
                klass._table = cls._table

        stacked_parents = [getattr(x, '_name', None) for x in cls.mro()]
        for name, field in cls._fields.items():
            if hasattr(field, 'comodel_name') and field.comodel_name:
                comodel_name = field.comodel_name
                comodel = self.env[comodel_name]
                concrete_class = cls._get_concrete(comodel._name)

                if not hasattr(comodel, '_concrete_rec_name'):
                    # TODO filter with klass._schema name instead?
                    continue

                if field.type == 'many2one' and concrete_class is not None\
                        and comodel_name not in stacked_parents:
                    _logger.debug("    MUTATING m2o %s (%s) -> %s",
                                  name, comodel_name, concrete_class)
                    field.original_comodel_name = comodel_name
                    field.comodel_name = concrete_class

                elif field.type == 'one2many':
                    if concrete_class is not None:
                        _logger.debug("    MUTATING o2m %s (%s) -> %s",
                                      name, comodel_name, concrete_class)
                        field.original_comodel_name = comodel_name
                        field.comodel_name = concrete_class
                    if not hasattr(field, 'inverse_name'):
                        continue
                    inv_name = field.inverse_name
                    for n, f in comodel._fields.items():
                        if n == inv_name and f.args.get('comodel_name'):
                            _logger.debug("    MUTATING m2o %s.%s (%s) -> %s",
                                          comodel._name.split('.')[-1], n,
                                          f.args['comodel_name'], cls._name)
                            f.args['original_comodel_name'] = f.args[
                                'comodel_name']
                            f.args['comodel_name'] = self._name

        return super()._setup_fields()

    @classmethod
    def _map_concrete(cls, key, target, quiet=False):
        # TODO bookkeep according to a key to allow multiple injection contexts
        if not hasattr(models.MetaModel, 'mixin_mappings'):
            models.MetaModel.mixin_mappings = {}
        if not quiet:
            _logger.debug("%s ---> %s" % (key, target))
        models.MetaModel.mixin_mappings[key] = target

    @classmethod
    def _get_concrete(cls, key):
        if not hasattr(models.MetaModel, 'mixin_mappings'):
            models.MetaModel.mixin_mappings = {}
        return models.MetaModel.mixin_mappings.get(key)

    @classmethod
    def spec_module_classes(cls, spec_module):
        """
        Cache the list of spec_module classes to save calls to
        slow reflection API.
        """
        spec_module_attr = "_spec_cache_%s" % (spec_module.replace('.', '_'),)
        if not hasattr(cls, spec_module_attr):
            setattr(
                cls, spec_module_attr, getmembers(sys.modules[spec_module], isclass)
            )
        return getattr(cls, spec_module_attr)

    @classmethod
    def _odoo_name_to_class(cls, odoo_name, spec_module):
        for name, base_class in cls.spec_module_classes(spec_module):
            if base_class._name == odoo_name:
                return base_class
        return None

    def _register_hook(self):
        res = super(SpecModel, self)._register_hook()
        load_key = "_%s_loaded" % (self._spec_module,)
        if not hasattr(self.env.registry, load_key):
            from .. import hooks  # importing here avoids loop
            hooks.register_hook(self.env, self._odoo_module, self._spec_module)
            self.env.registry.load_key = True
        return res


class StackedModel(SpecModel):
    """XML structures are typically deeply nested as this helps xsd
    validation. However, deeply nested objects in Odoo suck because that would
    mean crazy joins accross many tables and also an endless cascade of form
    popups. By inheriting from StackModel instead, your models.Model can
    instead inherit all the mixins that would correspond to the nested xsd
    nodes starting from the _stacked node. _stack_skip allows you to avoid
    stacking specific nodes. In Brazil it allows us to have mostly the fiscal
    document objects and the fiscal document line object with many details
    stacked in a denormalized way inside these two tables only.
    Because StackedModel has its _build_method overriden to do some magic
    during module loading it should be inherited the Python way
    with MyModel(spec_models.StackedModel).
    """
    _register = False  # forces you to inherit StackeModel properly

    # define _stacked in your submodel to define the model of the XML tags
    # where we should start to
    # stack models of nested tags in the same object.
    _stacked = False
    _stack_path = ""
    _stack_skip = ()
    # all m2o below these paths will be stacked even if not required:
    _force_stack_paths = ()
    _stacking_points = {}

    @classmethod
    def _build_model(cls, pool, cr):
        # inject all stacked m2o as inherited classes
        if cls._stacked:
            _logger.info("\n\n====  BUILDING StackedModel %s %s\n"
                         % (cls._name, cls))
            node = cls._odoo_name_to_class(cls._stacked, cls._spec_module)
            classes = set()
            cls._visit_stack(node, classes, cls._stacked.split('.')[-1], pool,
                             cr)
            for klass in [c for c in classes if c not in cls.__bases__]:
                cls.__bases__ = (klass,) + cls.__bases__
        return super(StackedModel, cls)._build_model(pool, cr)

    @api.model
    def _add_field(self, name, field):
        for cls in type(self).mro():
            if issubclass(cls, StackedModel):
                if name in type(self)._stacking_points.keys():
                    return
        return super()._add_field(name, field)

    @classmethod  # TODO rename with _
    def _visit_stack(cls, node, classes, path, registry, cr):
        """Pre-order traversal of the stacked models tree.
        1. This method is used to dynamically inherit all the spec models
        stacked together from an XML hierarchy.
        2. It is also useful to generate an automatic view of the spec fields.
        3. Finally it is used when exporting as XML.
        """
        # We are removing the description of the node
        # to avoid translations error
        # https://github.com/OCA/l10n-brazil/pull/1272#issuecomment-821806603
        node._description = None

        # TODO may be an option to print the stack (for debug)
        # after field mutation happened
        # path_items = path.split('.')
        # indent = '    '.join(['' for i in range(0, len(path_items) + 2)])

        concrete_model = SpecModel._get_concrete(node._name)
        if concrete_model is not None and concrete_model != cls._name:
            # we won't stack the class but leave the field
            # as a many2one relation to the existing Odoo class
            # were the class is already mapped
            # _logger.info("  %s<%s> %s" % (indent, path, concrete_model))
            return
        else:
            # ok we will stack the class
            SpecModel._map_concrete(node._name, cls._name, quiet=True)
            # _logger.info("%s> <%s>  <<-- %s" % (
            #     indent, path.split('.')[-1], node._name))
        classes.add(node)
        fields = collections.OrderedDict()
        env = api.Environment(cr, SUPERUSER_ID, {})
        # this is required when you don't start odoo with -i (update)
        # otherwise the model spec will not have its fields loaded yet.
        # TODO we may pass this env further instead of re-creating it.
        # TODO move setup_base just before the _visit_stack next call
        if node._name != cls._name or\
                len(registry[node._name]._fields.items() == 0):
            env[node._name]._prepare_setup()
            env[node._name]._setup_base()

        field_items = [(k, f) for k, f in registry[
            node._name]._fields.items()]
        for i in field_items:
            fields[i[0]] = {
                'type': i[1].type,
                # TODO get with a function (lambda?)
                'comodel_name': getattr(i[1], 'comodel_name'),
                'xsd_required': hasattr(
                    i[1], 'xsd_required') and getattr(i[1], 'xsd_required'),
                'choice': hasattr(i[1], 'choice') and getattr(i[1], 'choice'),
            }
        for name, f in fields.items():
            if f['type'] not in ['many2one', 'one2many']\
                    or name in cls._stack_skip:
                # TODO change for view or export
                continue
            child = cls._odoo_name_to_class(f['comodel_name'],
                                            cls._spec_module)
            if child is None:  # Not a spec field
                continue
            child_concrete = SpecModel._get_concrete(child._name)
            field_path = name.replace(registry[node._name]._field_prefix, '')
            if f['type'] == 'one2many':
                # _logger.info("%s    \u2261 <%s> %s" % (
                #     indent, field_path, child_concrete or child._name))
                continue
            # TODO this elif and next elif should in fact be replaced by the
            # inicial if where we look if node has a concrete model or not.
            # many2one
            elif (child_concrete is None or child_concrete == cls._name)\
                    and (f['xsd_required'] or f['choice']
                         or path in cls._force_stack_paths):
                # then we will STACK the child in the current class
                # TODO if model not used in any other field!!
                child._stack_path = path
                # field.args['_stack_path'] = path  TODO
                child_path = "%s.%s" % (path, field_path)
                cls._stacking_points[name] = registry[node._name]._fields.get(name)
                cls._visit_stack(child, classes, child_path, registry, cr)
            # else:
            #     if child_concrete:
            #         _logger.info("%s    - <%s>  -->%s " % (
            #             indent, field_path, child_concrete))
            #     else:
            #         _logger.info("%s    - <%s> %s" % (
            #             indent, field_path, child._name))
