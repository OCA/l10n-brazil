# Copyright 2019-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import sys
from collections import OrderedDict, defaultdict
from importlib import import_module
from inspect import getmembers, isclass

from odoo import SUPERUSER_ID, _, api, models
from odoo.tools import mute_logger

SPEC_MIXIN_MAPPINGS = defaultdict(dict)  # by db

_logger = logging.getLogger(__name__)


class SelectionMuteLogger(mute_logger):
    """
    The following fields.Selection warnings seem both very hard to
    avoid and benign in the spec_driven_model framework context.
    All in all, muting these 2 warnings seems like the best option.
    """

    def filter(self, record):
        msg = record.getMessage()
        if (
            "selection attribute will be ignored" in msg
            or "overrides existing selection" in msg
        ):
            return 0
        return super().filter(record)


class SpecModel(models.Model):
    """When you inherit this Model, then your model becomes concrete just like
    models.Model and it can use _inherit to inherit from several xsd generated
    spec mixins.
    All your model relational fields will be automatically mutated according to
    which concrete models the spec mixins where injected in.
    Because of this field mutation logic in _build_model, SpecModel should be
    inherited the Python way YourModel(spec_models.SpecModel)
    and not through _inherit.
    """

    _inherit = "spec.mixin"
    _auto = True  # automatically create database backend
    _register = False  # not visible in ORM registry
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
        res = super()._compute_display_name()
        for rec in self:
            if rec.display_name == "False" or not rec.display_name:
                rec.display_name = _("Open...")
        return res

    @classmethod
    def _build_model(cls, pool, cr):
        """
        xsd generated spec mixins do not need to depend on this opinionated
        module. That's why the spec.mixin is dynamically injected as a parent
        class as long as the generated spec mixins inherit from some
        spec.mixin.<schema_name> mixin.
        """
        if hasattr(cls, "_spec_schema"):  # when called via _register_hook
            schema = cls._spec_schema
        else:
            mod = import_module(".".join(cls.__module__.split(".")[:-1]))
            schema = mod.spec_schema

        if schema and "spec.mixin" not in [
            c._name for c in pool[f"spec.mixin.{schema}"].__bases__
        ]:
            spec_mixin = pool[f"spec.mixin.{schema}"]
            spec_mixin._inherit = list(spec_mixin._inherit) + ["spec.mixin"]
            spec_mixin._BaseModel__base_classes = (
                pool["spec.mixin"],
            ) + spec_mixin._BaseModel__base_classes
            spec_mixin.__bases__ = (pool["spec.mixin"],) + spec_mixin.__bases__

        parents = [
            item[0] if isinstance(item, list) else item for item in list(cls._inherit)
        ]
        for parent in parents:
            # this will register that the spec mixins where injected in this class
            cls._map_concrete(cr.dbname, parent, cls._name)
        return super()._build_model(pool, cr)

    @api.model
    def _setup_base(self):
        with SelectionMuteLogger("odoo.fields"):  # mute spurious warnings
            return super()._setup_base()

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
            if not hasattr(klass, "_is_spec_driven"):
                continue
            if klass._name != cls._name:
                cls._map_concrete(self.env.cr.dbname, klass._name, cls._name)
                klass._table = cls._table

        stacked_parents = [getattr(x, "_name", None) for x in cls.mro()]
        for name, field in cls._fields.items():
            if hasattr(field, "comodel_name") and field.comodel_name:
                comodel_name = field.comodel_name
                comodel = self.env[comodel_name]
                concrete_class = SPEC_MIXIN_MAPPINGS[self.env.cr.dbname].get(
                    comodel._name
                )

                if (
                    field.type == "many2one"
                    and concrete_class is not None
                    and comodel_name not in stacked_parents
                ):
                    _logger.debug(
                        "    MUTATING m2o %s (%s) -> %s",
                        name,
                        comodel_name,
                        concrete_class,
                    )
                    field.original_comodel_name = comodel_name
                    field.comodel_name = concrete_class

                elif field.type == "one2many":
                    if concrete_class is not None:
                        _logger.debug(
                            "    MUTATING o2m %s (%s) -> %s",
                            name,
                            comodel_name,
                            concrete_class,
                        )
                        field.original_comodel_name = comodel_name
                        field.comodel_name = concrete_class
                    if not hasattr(field, "inverse_name"):
                        continue
                    inv_name = field.inverse_name
                    for n, f in comodel._fields.items():
                        if n == inv_name and f.args and f.args.get("comodel_name"):
                            _logger.debug(
                                "    MUTATING m2o %s.%s (%s) -> %s",
                                comodel._name.split(".")[-1],
                                n,
                                f.args["comodel_name"],
                                cls._name,
                            )
                            f.args["original_comodel_name"] = f.args["comodel_name"]
                            f.args["comodel_name"] = self._name

        return super()._setup_fields()

    @classmethod
    def _map_concrete(cls, dbname, key, target, quiet=False):
        if not quiet:
            _logger.debug(f"{key} ---> {target}")
        global SPEC_MIXIN_MAPPINGS
        SPEC_MIXIN_MAPPINGS[dbname][key] = target

    @classmethod
    def spec_module_classes(cls, spec_module):
        """
        Cache the list of spec_module classes to save calls to
        slow reflection API.
        """
        spec_module_attr = f"_spec_cache_{spec_module.replace('.', '_')}"
        if not hasattr(cls, spec_module_attr):
            setattr(
                cls, spec_module_attr, getmembers(sys.modules[spec_module], isclass)
            )
        return getattr(cls, spec_module_attr)

    @classmethod
    def _odoo_name_to_class(cls, odoo_name, spec_module):
        for _name, base_class in cls.spec_module_classes(spec_module):
            if base_class._name == odoo_name:
                return base_class
        return None


class StackedModel(SpecModel):
    """
    XML structures are typically deeply nested as this helps xsd
    validation. However, deeply nested objects in Odoo suck because that would
    mean crazy joins accross many tables and also an endless cascade of form
    popups.

    By inheriting from StackModel instead, your models.Model can
    instead inherit all the mixins that would correspond to the nested xsd
    nodes starting from the stacking_mixin. stacking_skip_paths allows you to avoid
    stacking specific nodes while stacking_force_paths will stack many2one
    entities even if they are not required.

    In Brazil it allows us to have mostly the fiscal
    document objects and the fiscal document line object with many details
    stacked in a denormalized way inside these two tables only.
    Because StackedModel has its _build_method overriden to do some magic
    during module loading it should be inherited the Python way
    with MyModel(spec_models.StackedModel).
    """

    _register = False  # forces you to inherit StackeModel properly

    @classmethod
    def _build_model(cls, pool, cr):
        if hasattr(cls, "_spec_schema"):  # when called via _register_hook
            schema = cls._spec_schema
            version = cls._spec_version.replace(".", "")[:2]
        else:
            mod = import_module(".".join(cls.__module__.split(".")[:-1]))
            schema = mod.spec_schema
            version = mod.spec_version.replace(".", "")[:2]
        spec_prefix = f"{schema}{version}"
        setattr(cls, f"_{spec_prefix}_stacking_points", {})
        stacking_settings = {
            "odoo_module": getattr(cls, f"_{spec_prefix}_odoo_module"),  # TODO inherit?
            "stacking_mixin": getattr(cls, f"_{spec_prefix}_stacking_mixin"),
            "stacking_points": getattr(cls, f"_{spec_prefix}_stacking_points"),
            "stacking_skip_paths": getattr(
                cls, f"_{spec_prefix}_stacking_skip_paths", []
            ),
            "stacking_force_paths": getattr(
                cls, f"_{spec_prefix}_stacking_force_paths", []
            ),
        }
        # inject all stacked m2o as inherited classes
        _logger.info(f"building StackedModel {cls._name} {cls}")
        node = cls._odoo_name_to_class(
            stacking_settings["stacking_mixin"], stacking_settings["odoo_module"]
        )
        env = api.Environment(cr, SUPERUSER_ID, {})
        for kind, klass, _path, _field_path, _child_concrete in cls._visit_stack(
            env, node, stacking_settings
        ):
            if kind == "stacked" and klass not in cls.__bases__:
                cls.__bases__ = (klass,) + cls.__bases__
        return super()._build_model(pool, cr)

    @api.model
    def _add_field(self, name, field):
        """
        Overriden to avoid adding many2one fields that are in fact "stacking points"
        """
        if field.type == "many2one":
            for cls in type(self).mro():
                if issubclass(cls, StackedModel):
                    for attr in dir(cls):
                        if attr != "_get_stacking_points" and attr.endswith(
                            "_stacking_points"
                        ):
                            if name in getattr(cls, attr).keys():
                                # TODO it seems Odoo would still generate ir.model.data
                                # records for these fields we skip. They are deleted
                                # in IrModelData#_process_end. Eventually we could
                                # avoid creating these records or delete them.
                                return
        return super()._add_field(name, field)

    @classmethod
    def _visit_stack(cls, env, node, stacking_settings, path=None):
        """Pre-order traversal of the stacked models tree.
        1. This method is used to dynamically inherit all the spec models
        stacked together from an XML hierarchy.
        2. It is also useful to generate an automatic view of the spec fields.
        3. Finally it is used when exporting as XML.
        """
        if path is None:
            path = stacking_settings["stacking_mixin"].split(".")[-1]
        cls._map_concrete(env.cr.dbname, node._name, cls._name, quiet=True)
        yield "stacked", node, path, None, None

        fields = OrderedDict()
        # this is required when you don't start odoo with -i (update)
        # otherwise the model spec will not have its fields loaded yet.
        # TODO we may pass this env further instead of re-creating it.
        # TODO move setup_base just before the _visit_stack next call
        if node._name != cls._name or len(env[node._name]._fields.items() == 0):
            env[node._name]._prepare_setup()
            env[node._name]._setup_base()

        field_items = [(k, f) for k, f in env[node._name]._fields.items()]
        for i in field_items:
            fields[i[0]] = {
                "type": i[1].type,
                # TODO get with a function (lambda?)
                "comodel_name": i[1].comodel_name,
                "xsd_required": hasattr(i[1], "xsd_required") and i[1].xsd_required,
                "xsd_choice_required": hasattr(i[1], "xsd_choice_required")
                and i[1].xsd_choice_required,
            }
        for name, f in fields.items():
            if f["type"] not in [
                "many2one",
                "one2many",
            ] or name in stacking_settings.get("stacking_skip_paths", ""):
                # TODO change for view or export
                continue
            child = cls._odoo_name_to_class(
                f["comodel_name"], stacking_settings["odoo_module"]
            )
            if child is None:  # Not a spec field
                continue
            child_concrete = SPEC_MIXIN_MAPPINGS[env.cr.dbname].get(child._name)
            field_path = name.split("_")[1]  # remove schema prefix

            if f["type"] == "one2many":
                yield "one2many", node, path, field_path, child_concrete
                continue

            force_stacked = any(
                stack_path in path + "." + field_path
                for stack_path in stacking_settings.get("stacking_force_paths", [])
            )

            # many2one
            if (child_concrete is None or child_concrete == cls._name) and (
                f["xsd_required"] or f["xsd_choice_required"] or force_stacked
            ):
                # then we will STACK the child in the current class
                child._stack_path = path
                child_path = f"{path}.{field_path}"
                stacking_settings["stacking_points"][name] = env[
                    node._name
                ]._fields.get(name)
                yield from cls._visit_stack(env, child, stacking_settings, child_path)
            else:
                yield "many2one", node, path, field_path, child_concrete
