# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_partner_to_invoice(self):
        """
        If the partner has some invoicing contact defined
        partner_invoice_id is auto filled, but it can also be changed.
        partner_invoice_id is used if different from partner_id
        """
        self.ensure_one()
        partner_id = super()._get_partner_to_invoice()
        if self.sale_id:
            if partner_id != self.sale_id.partner_invoice_id.id:
                partner_id = self.sale_id.partner_invoice_id.id
        return partner_id

    def _get_fiscal_partner(self):
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        if partner != self._get_partner_to_invoice():
            partner = self._get_partner_to_invoice()
        return partner
