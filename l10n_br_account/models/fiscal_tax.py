# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, api


class FiscalTax(models.Model):
    _inherit = 'l10n_br_fiscal.tax'

    @api.model
    def create(self, values):
        if not values.get('partner_id'):
            self.clear_caches()
            return super(FiscalTax, self).create(values)
