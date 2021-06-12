# Copyright (C) 2009  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    fiscal_tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Fiscal Tax Group",
    )
