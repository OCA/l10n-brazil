# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalTaxGroup(models.Model):
    _inherit = "l10n_br_fiscal.tax.group"

    colect_account_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Tax Account',
        company_dependent=True,
        ondelete='restrict')

    recover_account_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Tax Account on Credit Notes',
        company_dependent=True,
        ondelete='restrict')

    @api.model
    def create(self, values):
        if not values.get("partner_id"):
            self.clear_caches()
            return super(FiscalTax, self).create(values)
