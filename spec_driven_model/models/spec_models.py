# Copyright 2019-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import logging
import sys
from collections import OrderedDict, defaultdict
from importlib import import_module
from inspect import getmembers, isclass

from odoo import _, api, models
from odoo.api import Environment
from odoo.orm import model_classes
from odoo.tools import mute_logger

from .ir_model import disambiguate_spec_labels

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


def _module_spec_attrs(cls):
    """spec_schema and spec_version declared on the package of a class."""
    if hasattr(cls, "_spec_schema"):  # set on the remaining models we build
        return cls._spec_schema, getattr(cls, "_spec_version", None)
    mod = import_module(".".join(cls.__module__.split(".")[:-1]))
    return getattr(mod, "spec_schema", None), getattr(mod, "spec_version", None)


def _inject_spec_mixin(registry, schema):
    """Make spec.mixin a parent of the spec.mixin.<schema> registry class.

    xsd generated spec mixins do not need to depend on this opinionated
    module. That's why spec.mixin is dynamically injected as a parent
    class as long as the generated spec mixins inherit from some
    spec.mixin.<schema_name> mixin. Idempotent.
    """
    name = f"spec.mixin.{schema}"
    if name not in registry or "spec.mixin" not in registry:
        return
    mixin_cls = registry[name]
    parent_cls = registry["spec.mixin"]
    if parent_cls in mixin_cls._base_classes__:
        return
    mixin_cls._inherit = list(mixin_cls._inherit) + ["spec.mixin"]
    # __bases__ is assigned from _base_classes__ when the model is set up
    # (model_classes._prepare_setup)
    mixin_cls._base_classes__ = (parent_cls,) + tuple(mixin_cls._base_classes__)
    mixin_cls._inherit_module["spec.mixin"] = "spec_driven_model"
    parent_cls._inherit_children.add(name)
    for model_name in registry.descendants([name], "_inherit", "_inherits"):
        registry[model_name]._setup_done__ = False
    # apply the new parent right away: the models built while the registry is
    # already set up (remaining models) must see it in their MRO
    model_classes._prepare_setup(mixin_cls)


def _definition_fields(registry, model_name):
    """Fields of a model as declared by its definition classes.

    The registry class of a model gets its fields only when it is set up,
    which happens after all the modules are loaded. The stacking of
    StackedModel must be known before that (it defines the parents of the
    model), so we read the field definitions like model_classes._setup would:
    the last definition of a field wins, in the order of the MRO.
    """
    model_cls = registry[model_name]
    model_classes._prepare_setup(model_cls)
    result = OrderedDict()
    for klass in reversed(model_cls.mro()):
        if isinstance(klass, models.MetaModel) and model_classes.is_model_definition(
            klass
        ):
            for field in klass._field_definitions:
                result[field.name] = field
    return result


def _field_attr(field, name):
    """A field parameter, before or after the setup of the field."""
    value = getattr(field, name, None)
    if value is None and getattr(field, "_args__", None):
        value = field._args__.get(name)
    return value


def _replace_relational_field(model_cls, name, comodel_name):
    """Recreate the field `name` of model_cls pointing to comodel_name.

    The field object may be shared (a definition field, or a shared registry
    field in more recent Odoo versions), so we never mutate it: we build a new
    field from the same definitions with the comodel overridden, as
    model_classes._setup does for overridden fields.
    """
    field = model_cls._fields[name]
    if field.comodel_name == comodel_name:
        return
    definitions = [
        definition
        for klass in reversed(model_cls._model_classes__)
        for definition in getattr(klass, "_field_definitions", ())
        if definition.name == name
    ]
    if not definitions:
        return
    new_field = type(field)(
        _base_fields__=tuple(definitions),
        comodel_name=comodel_name,
        original_comodel_name=field.comodel_name,
    )
    model_classes.add_field(model_cls, name, new_field)
    new_field.prepare_setup()


class SpecModel(models.Model):
    """When you inherit this Model, then your model becomes concrete just like
    models.Model and it can use _inherit to inherit from several xsd generated
    spec mixins.
    All your model relational fields will be automatically mutated according to
    which concrete models the spec mixins where injected in.
    Because of this field mutation logic in _spec_setup, SpecModel should be
    inherited the Python way YourModel(spec_models.SpecModel)
    and not through _inherit.
    """

    _inherit = ["spec.mixin"]
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
    def _spec_before_add_to_registry(cls, registry):
        """
        Called with the model definition class right before Odoo adds it to
        the registry (it replaces the _build_model override of Odoo <= 18).
        It injects spec.mixin in the spec.mixin.<schema> mixin and registers
        in which concrete model the spec mixins are injected.
        """
        # In Odoo 18+, the test framework monitors model attribute modifications
        # and logs stack traces. We suppress these during dynamic model building.
        with mute_logger("odoo.tests.common"):
            schema, _version = _module_spec_attrs(cls)
            if schema:
                _inject_spec_mixin(registry, schema)
            parents = [
                item[0] if isinstance(item, list) else item
                for item in list(cls._inherit)
            ]
            for parent in parents:
                # this will register that the spec mixins where injected in this class
                cls._map_concrete(registry.db_name, parent, cls._name)

    @classmethod
    def _spec_setup(cls, env):
        """
        Called on the registry class once model_classes._setup determined its
        fields, and before they are set up (it replaces the _setup_fields
        override of Odoo <= 18).

        SpecModel models inherit their fields from XSD generated mixins.
        These mixins can either be made concrete, either be injected into
        existing concrete Odoo models. In that last case, the comodels of the
        relational fields pointing to such mixins should be remapped to the
        proper concrete models where these mixins are injected.
        """
        registry = cls.pool
        mappings = SPEC_MIXIN_MAPPINGS[registry.db_name]
        for klass in cls.__bases__:
            if not hasattr(klass, "_is_spec_driven"):
                continue
            if klass._name != cls._name:
                cls._map_concrete(registry.db_name, klass._name, cls._name)
                with mute_logger("odoo.tests.common"):
                    klass._table = cls._table

        stacked_parents = [getattr(x, "_name", None) for x in cls.mro()]
        for name, field in list(cls._fields.items()):
            comodel_name = getattr(field, "comodel_name", None)
            if not comodel_name:
                continue
            concrete_class = mappings.get(comodel_name)

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
                _replace_relational_field(cls, name, concrete_class)

            elif field.type == "one2many":
                if concrete_class is not None:
                    _logger.debug(
                        "    MUTATING o2m %s (%s) -> %s",
                        name,
                        comodel_name,
                        concrete_class,
                    )
                    _replace_relational_field(cls, name, concrete_class)
                inv_name = field.inverse_name
                comodel_cls = registry.get(concrete_class or comodel_name)
                if not inv_name or comodel_cls is None:
                    continue
                # the inverse many2one of the concrete comodel still points to
                # the spec mixin stacked into this model: point it to this model
                model_classes._prepare_setup(comodel_cls)
                model_classes._setup(comodel_cls, env)
                inv_field = comodel_cls._fields.get(inv_name)
                if (
                    inv_field is not None
                    and inv_field.type == "many2one"
                    and not inv_field.related
                    and inv_field.comodel_name != cls._name
                    and inv_field.comodel_name in stacked_parents
                ):
                    _logger.debug(
                        "    MUTATING m2o %s.%s (%s) -> %s",
                        comodel_cls._name.split(".")[-1],
                        inv_name,
                        inv_field.comodel_name,
                        cls._name,
                    )
                    _replace_relational_field(comodel_cls, inv_name, cls._name)

        disambiguate_spec_labels(cls)

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
            # In Odoo 18+, the test framework monitors model attribute modifications
            # and logs stack traces. We suppress these during dynamic model building.
            with mute_logger("odoo.tests.common"):
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
    Because StackedModel does some magic before being added to the registry
    it should be inherited the Python way with MyModel(spec_models.StackedModel).
    """

    _register = False  # forces you to inherit StackeModel properly

    @classmethod
    def _spec_before_add_to_registry(cls, registry):
        # In Odoo 18+, the test framework monitors model attribute modifications
        # and logs stack traces. We suppress these during dynamic model building.
        with mute_logger("odoo.tests.common"):
            schema, version = _module_spec_attrs(cls)
            version = version.replace(".", "")[:2]
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
        with mute_logger("odoo.tests.common"):
            for kind, klass, _path, _field_path, _child_concrete in cls._visit_stack(
                registry, node, stacking_settings
            ):
                if kind == "stacked" and klass._name not in cls._inherit:
                    cls._inherit.append(klass._name)
        return super()._spec_before_add_to_registry(registry)

    @classmethod
    def _spec_setup(cls, env):
        """
        Remove the many2one fields that are in fact "stacking points": their
        comodel content is stacked in this model.
        """
        for klass in cls.mro():
            if not issubclass(klass, StackedModel):
                continue
            for attr in dir(klass):
                if attr != "_get_stacking_points" and attr.endswith("_stacking_points"):
                    for name in getattr(klass, attr).keys():
                        field = cls._fields.get(name)
                        if field is not None and field.type == "many2one":
                            # TODO it seems Odoo would still generate ir.model.data
                            # records for these fields we skip. They are deleted
                            # in IrModelData#_process_end. Eventually we could
                            # avoid creating these records or delete them.
                            model_classes.pop_field(cls, name)
        return super()._spec_setup(env)

    @classmethod
    def _visit_stack(cls, env, node, stacking_settings, path=None):
        """Pre-order traversal of the stacked models tree.
        1. This method is used to dynamically inherit all the spec models
        stacked together from an XML hierarchy.
        2. It is also useful to generate an automatic view of the spec fields.
        3. Finally it is used when exporting as XML.
        `env` is an Environment, or the Registry while the model is being
        added to the registry.
        """
        registry = env.registry if isinstance(env, Environment) else env
        if path is None:
            path = stacking_settings["stacking_mixin"].split(".")[-1]
        cls._map_concrete(registry.db_name, node._name, cls._name, quiet=True)
        yield "stacked", node, path, None, None

        node_fields = _definition_fields(registry, node._name)
        fields = OrderedDict()
        for name, field in node_fields.items():
            fields[name] = {
                "type": field.type,
                "comodel_name": _field_attr(field, "comodel_name"),
                "xsd_required": bool(_field_attr(field, "xsd_required")),
                "xsd_choice_required": bool(_field_attr(field, "xsd_choice_required")),
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
            child_concrete = SPEC_MIXIN_MAPPINGS[registry.db_name].get(child._name)
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
                # In Odoo 18+, the test framework monitors model attribute modifications
                # and logs stack traces. We suppress these during dynamic model building
                with mute_logger("odoo.tests.common"):
                    child._stack_path = path
                child_path = f"{path}.{field_path}"
                stacking_settings["stacking_points"][name] = node_fields[name]
                yield from cls._visit_stack(env, child, stacking_settings, child_path)
            else:
                yield "many2one", node, path, field_path, child_concrete


# Odoo 19 builds the model classes with plain functions of
# odoo.orm.model_classes instead of overridable class methods (_build_model,
# _setup_base, _setup_fields). spec_driven_model needs to act at the same two
# points as before, so it wraps these two functions and calls the class hooks
# above for SpecModel classes only; every other model goes through untouched.
_original_add_to_registry = model_classes.add_to_registry
_original_setup = model_classes._setup


def _spec_add_to_registry(registry, model_def):
    if issubclass(model_def, SpecModel):
        model_def._spec_before_add_to_registry(registry)
    return _original_add_to_registry(registry, model_def)


def _setup_with_spec(model_cls, env):
    if model_cls._setup_done__ or not issubclass(model_cls, SpecModel):
        return _original_setup(model_cls, env)
    with SelectionMuteLogger("odoo.fields"):  # mute spurious warnings
        _original_setup(model_cls, env)
    model_cls._spec_setup(env)


if not getattr(model_classes.add_to_registry, "_spec_driven", False):
    _spec_add_to_registry._spec_driven = True
    _setup_with_spec._spec_driven = True
    model_classes.add_to_registry = _spec_add_to_registry
    model_classes._setup = _setup_with_spec
