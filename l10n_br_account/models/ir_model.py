# Copyright (C) 2026 - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, models
from odoo.tools import OrderedSet

_logger = logging.getLogger(__name__)


class ModelInherit(models.Model):
    _inherit = "ir.model.inherit"

    @api.model
    def _reflect_inherits(self, model_names):
        # Ensure all parent models referenced by the given model_names are already
        # reflected in ir_model before the core _reflect_inherits method inserts
        # ir_model_inherit rows.
        #
        # This fixes a compatibility issue where modules like account_edi_ubl_cii have
        # new abstract models that are not reflected in older databases, and a later
        # dependent module (e.g. sale_edi_ubl) tries to inherit from them. Without this
        # fix, the reflection insert would fail with a NOT NULL violation on parent_id.
        registry = self.env.registry
        missing = OrderedSet()
        for model_name in model_names:
            model = self.env[model_name]
            for cls in reversed(type(model).mro()):
                if not models.is_definition_class(cls):
                    continue
                parents = cls._inherit or []
                if isinstance(parents, str):
                    parents = [parents]
                for parent in parents:
                    if parent in ("base", model_name):
                        continue
                    if registry.get(parent) and not self.env["ir.model"]._get_id(
                        parent
                    ):
                        missing.add(parent)
                for parent in cls._inherits:
                    if registry.get(parent) and not self.env["ir.model"]._get_id(
                        parent
                    ):
                        missing.add(parent)
        if missing:
            _logger.warning(
                "Forcing reflection of missing parent models "
                "so ir_model_inherit can proceed: %s",
                list(missing),
            )
            self.env["ir.model"]._reflect_models(list(missing))
            self.env.registry.clear_cache()
        return super()._reflect_inherits(model_names)
