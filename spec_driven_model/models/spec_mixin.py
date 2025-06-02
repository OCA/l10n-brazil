# Copyright 2019-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from importlib import import_module

from odoo import api, models
from odoo.tools import mute_logger

from .spec_models import SPEC_MIXIN_MAPPINGS, SpecModel, StackedModel


class SpecMixin(models.AbstractModel):
    """
    This is the root "spec" mixin that will be injected dynamically as the parent
    of your custom schema mixin (such as spec.mixin.nfe) without the need that
    your spec mixin depend on this mixin and on the spec_driven_model module directly
    (loose coupling).
    This root mixin is typically injected via the _build_model method from SpecModel
    or StackedModel that you will be using to inject some spec mixins into
    existing Odoo objects. spec.mixin provides generic utility methods such as a
    _register_hook, import and export methods.
    """

    _description = "root abstract model meant for xsd generated fiscal models"
    _name = "spec.mixin"
    _inherit = ["spec.mixin_export", "spec.mixin_import"]
    _is_spec_driven = True

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_choice_required",
            "xsd_implicit",
            "original_comodel_name",
        ):
            return True
        else:
            return super()._valid_field_parameter(field, name)

    @api.model
    def _get_concrete_model(self, model_name):
        "Lookup for concrete models where abstract schema mixins were injected"
        if SPEC_MIXIN_MAPPINGS[self.env.cr.dbname].get(model_name) is not None:
            return self.env[SPEC_MIXIN_MAPPINGS[self.env.cr.dbname].get(model_name)]
        else:
            return self.env.get(model_name)

    def _spec_prefix(self, split=False):
        """
        Get spec_schema and spec_version from context or from class module
        """
        if self._context.get("spec_schema") and self._context.get("spec_version"):
            spec_schema = self._context.get("spec_schema")
            spec_version = self._context.get("spec_version")
            if spec_schema and spec_version:
                spec_version = spec_version.replace(".", "")[:2]
                if split:
                    return spec_schema, spec_version
                return f"{spec_schema}{spec_version}"

        for ancestor in type(self).mro():
            if not ancestor.__module__.startswith("odoo.addons."):
                continue
            mod = import_module(".".join(ancestor.__module__.split(".")[:-1]))
            if hasattr(mod, "spec_schema"):
                spec_schema = mod.spec_schema
                spec_version = mod.spec_version.replace(".", "")[:2]
                if split:
                    return spec_schema, spec_version
                return f"{spec_schema}{spec_version}"

        return None, None if split else None

    def _get_spec_property(self, spec_property="", fallback=None):
        """
        Used to access schema wise and version wise automatic mappings properties
        """
        return getattr(self, f"_{self._spec_prefix()}_{spec_property}", fallback)

    def _get_stacking_points(self):
        return self._get_spec_property("stacking_points", {})

    def _register_hook(self):
        """
        Called once all modules are loaded.
        Here we take all spec models that were not injected into existing concrete
        Odoo models and we make them concrete automatically with
        their _auto_init method that will create their SQL DDL structure.
        """
        res = super()._register_hook()
        spec_schema, spec_version = self._spec_prefix(split=True)
        if not spec_schema:
            return res

        spec_module = self._get_spec_property("odoo_module")
        if "_spec." in spec_module:
            odoo_module = spec_module.split("_spec.")[0].split(".")[-1]
        else:  # for tests:
            odoo_module = "spec_driven_model"
        load_key = f"_{spec_module}_loaded"
        if hasattr(self.env.registry, load_key):  # hook already done for registry
            return res
        setattr(self.env.registry, load_key, True)

        access_data = []
        access_fields = []
        field_prefix = f"{spec_schema}{spec_version}"
        relation_prefix = f"{spec_schema}.{spec_version}.%"
        self.env.cr.execute(
            """SELECT DISTINCT relation FROM ir_model_fields
                   WHERE relation LIKE %s;""",
            (relation_prefix,),
        )
        # now we will filter only the spec models not injected into some existing class:
        remaining_models = {
            i[0]
            for i in self.env.cr.fetchall()
            if self.env.registry.get(i[0])
            and not SPEC_MIXIN_MAPPINGS[self.env.cr.dbname].get(i[0])
        }
        for name in remaining_models:
            spec_class = StackedModel._odoo_name_to_class(name, spec_module)
            if spec_class is None:
                continue
            fields = self.env[spec_class._name]._fields
            rec_name = next(
                filter(
                    lambda x: (x.startswith(field_prefix) and "_choice" not in x),
                    fields,
                ),
                None,
            )
            model_type = type(
                name,
                (SpecModel, spec_class),
                {
                    "_name": name,
                    "_inherit": spec_class._inherit,
                    "_original_module": odoo_module,
                    "_rec_name": rec_name,
                    "_module": odoo_module,
                },
            )
            # we set _spec_schema and _spec_version because
            # _build_model will not have context access:
            model_type._spec_schema = spec_schema
            model_type._spec_version = spec_version
            models.MetaModel.module_to_models[odoo_module] += [model_type]

            # now we init these models properly
            # a bit like odoo.modules.loading#load_module_graph would do
            model = model_type._build_model(self.env.registry, self.env.cr)

            self.env[name]._prepare_setup()
            self.env[name]._setup_base()
            self.env[name]._setup_fields()
            self.env[name]._setup_complete()

            access_fields = [
                "id",
                "name",
                "model_id/id",
                "group_id/id",
                "perm_read",
                "perm_write",
                "perm_create",
                "perm_unlink",
            ]
            model._auto_fill_access_data(self.env, odoo_module, access_data)

        self.env["ir.model.access"].load(access_fields, access_data)
        self.env.registry.init_models(
            self.env.cr, remaining_models, {"module": odoo_module}
        )

        # init_models just created ir.model.data records for the "MAGIC FIELDS"
        # of the remaining_models. If we let these fields, next Odoo update
        # will decide that these MAGIC FIELDS do not match the fields of the
        # abstract schema mixins and would take a long time to delete these records
        # and the fields. This is not what we want, so we just remove these records:
        imd_magic_field_names = []
        for model in remaining_models:
            for field in models.MAGIC_COLUMNS + ["display_name", "__last_update"]:
                imd_magic_field_names.append(
                    f"field_{model.replace('.', '_')}__{field}"
                )
        imd_recs = self.env["ir.model.data"].search(
            [("name", "in", imd_magic_field_names)]
        )
        with mute_logger("odoo.models"):
            imd_recs.unlink()

        return res

    @classmethod
    def _auto_fill_access_data(cls, env, module_name: str, access_data: list):
        """
        Fill access_data with a default user and a default manager access.
        """

        underline_name = cls._name.replace(".", "_")
        if module_name == "spec_driven_model":
            model_id = f"spec_driven_model.model_{underline_name}"
        else:
            model_id = f"{module_name}_spec.model_{underline_name}"
        user_access_name = f"access_{underline_name}_user"
        if not env["ir.model.access"].search(
            [
                ("name", "in", [underline_name, user_access_name]),
                ("model_id", "=", model_id),
            ]
        ):
            access_data.append(
                [
                    user_access_name,
                    user_access_name,
                    model_id,
                    f"{module_name}.group_user",
                    "1",
                    "0",
                    "0",
                    "0",
                ]
            )
        manager_access_name = f"access_{underline_name}_manager"
        if not env["ir.model.access"].search(
            [
                ("name", "in", [underline_name, manager_access_name]),
                ("model_id", "=", model_id),
            ]
        ):
            access_data.append(
                [
                    manager_access_name,
                    manager_access_name,
                    model_id,
                    f"{module_name}.group_manager",
                    "1",
                    "1",
                    "1",
                    "1",
                ]
            )
