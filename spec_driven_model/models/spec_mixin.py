# Copyright 2019-2020 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import models


class SpecMixin(models.AbstractModel):
    """putting this mixin here makes it possible for generated schemas mixins
    to be installed without depending on the fiscal module.
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
