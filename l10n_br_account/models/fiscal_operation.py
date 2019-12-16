# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Account Journal",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('type', 'in', {'out': ['sale'], 'in': "
               "['purchase'], 'all': ['sale', 'purchase']}.get("
               "operation_type, []))]")
