# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, models
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class InheritsCheckMuteLogger(mute_logger):
    """
    Mute the Model#_inherits_check warning
    because the _inherits field is not required.
    (some account.move may have no fiscal document)
    """

    def filter(self, record):
        msg = record.getMessage()
        if "Field definition for _inherits reference" in msg:
            return 0
        return super().filter(record)


class FiscalDecoratorMixin(models.AbstractModel):
    _name = "l10n_br_account.decorator.mixin"
    _description = """A mixin to decorate l10n_br_fiscal_document(.line) easily.
    It specially deals with related and compute fields inherited with _inherits.
    """
    _fiscal_decorator_model = None

    @api.model
    def _inherits_check(self):
        """
        Overriden to avoid the super method to set the fiscal_document(_line)_id
        field as required.
        """
        with InheritsCheckMuteLogger("odoo.models"):  # mute spurious warnings
            res = super()._inherits_check()
        if self._fiscal_decorator_model is not None:
            field_name = self._inherits[self._fiscal_decorator_model]
            field = self._fields.get(field_name)
            field.required = False  # unset the required = True assignement
        return res

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(create_from_account=True)
        return super().create(vals_list)
