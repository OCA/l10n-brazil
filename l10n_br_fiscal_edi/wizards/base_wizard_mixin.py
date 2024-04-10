# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseWizardMixin(models.TransientModel):
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event",
        string="Fiscal Event",
    )
