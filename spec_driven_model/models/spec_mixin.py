# Copyright 2019-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import api, models

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
    _stacking_points = {}
    # _spec_module = 'override.with.your.python.module'
    # _binding_module = 'your.pyhthon.binding.module'
    # _odoo_module = 'your.odoo_module'
    # _field_prefix = 'your_field_prefix_'
    # _schema_name = 'your_schema_name'

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "xsd_required",
            "choice",
            "xsd_choice_required",
            "xsd_implicit",
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

    def _register_hook(self):
        """
        Called once all modules are loaded.
        Here we take all spec models that are not injected into existing concrete
        Odoo models and we make them concrete automatically with
        their _auto_init method that will create their SQL DDL structure.
        """
        res = super()._register_hook()
        if not hasattr(self, "_spec_module"):
            return res

        load_key = "_%s_loaded" % (self._spec_module,)
        if hasattr(self.env.registry, load_key):  # already done for registry
            return res
        setattr(self.env.registry, load_key, True)
        access_data = []
        access_fields = []
        self.env.cr.execute(
            """SELECT DISTINCT relation FROM ir_model_fields
                   WHERE relation LIKE %s;""",
            (f"{self._schema_name}.{self._schema_version.replace('.', '')[:2]}.%",),
        )
        # now we will filter only the spec models not injected into some existing class:
        remaining_models = {
            i[0]
            for i in self.env.cr.fetchall()
            if self.env.registry.get(i[0])
            and not SPEC_MIXIN_MAPPINGS[self.env.cr.dbname].get(i[0])
        }
        for name in remaining_models:
            spec_class = StackedModel._odoo_name_to_class(name, self._spec_module)
            if spec_class is None:
                continue
            spec_class._module = "fiscal"  # TODO use python_module ?
            fields = self.env[spec_class._name].fields_get_keys()
            rec_name = next(
                filter(
                    lambda x: (
                        x.startswith(self.env[spec_class._name]._field_prefix)
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
                    "_odoo_module": self._odoo_module,
                    "_spec_module": self._spec_module,
                    "_rec_name": rec_name,
                    "_module": self._odoo_module,
                },
            )
            models.MetaModel.module_to_models[self._odoo_module] += [model_type]

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
            model._auto_fill_access_data(self.env, self._odoo_module, access_data)

        self.env["ir.model.access"].load(access_fields, access_data)
        self.env.registry.init_models(
            self.env.cr, remaining_models, {"module": self._odoo_module}
        )
        return res

    @classmethod
    def _auto_fill_access_data(cls, env, module_name: str, access_data: list):
        """
        Fill access_data with a default user and a default manager access.
        """

        underline_name = cls._name.replace(".", "_")
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
