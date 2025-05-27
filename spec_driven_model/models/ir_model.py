# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import models
from odoo.tools import mute_logger


class IrModelFields(models.Model):
    """
    The two fields have the same label warnings in _reflect_fields
    seems abusive when two XSD schemas inject fields with the same label
    into the same Odoo object. So we silent them for the spec models.
    """

    _inherit = "ir.model.fields"

    def _is_spec_driven_model(self, model_name, visited=None):
        """Recursively check if model or any inherited model is spec-driven"""
        if visited is None:
            visited = set()

        if model_name in visited:
            return False

        visited.add(model_name)
        model = self.env[model_name]

        if hasattr(model, "_is_spec_driven"):
            return True

        return any(
            self._is_spec_driven_model(inherited_name, visited)
            for inherited_name in model._inherits.keys()
        )

    def _reflect_fields(self, model_names):
        spec_model_names = []
        non_spec_model_names = []

        for model_name in model_names:
            if self._is_spec_driven_model(model_name):
                spec_model_names.append(model_name)
            else:
                non_spec_model_names.append(model_name)

        with mute_logger("odoo.addons.base.models.ir_model"):
            # ir_model has only two warnings and the other one
            # is not in this call stack, so we can silent all
            # ir_model warnings quite safely here
            super()._reflect_fields(spec_model_names)

        return super()._reflect_fields(non_spec_model_names)
