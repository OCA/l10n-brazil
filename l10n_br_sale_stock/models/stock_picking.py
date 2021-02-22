# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_partner_to_invoice(self):
        self.ensure_one()
        partner = self.partner_id
        if self.sale_id:
            partner = self.sale_id.partner_invoice_id
        return partner.address_get(['invoice']).get('invoice')
