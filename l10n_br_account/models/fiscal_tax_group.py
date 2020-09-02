# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class FiscalTaxGroup(models.Model):
    _inherit = 'l10n_br_fiscal.tax.group'

    @api.multi
    def account_tax_group(self):
        self.ensure_one()
        return self.env['account.tax.group'].search(
            [('fiscal_tax_group_id', 'in', self.ids)], limit=1)
