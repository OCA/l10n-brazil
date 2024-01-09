# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_partner_to_invoice(self):
        self.ensure_one()
        partner_id = super()._get_partner_to_invoice()
        if self.sale_id:
            # Caso Vendas, a prioridade é do campo informado
            # pelo usuário, quando o Partner tem um contato
            # definido como Tipo Invoice o campo partner_invoice_id
            # é preenchido com esse valor automaticamente
            if partner_id != self.sale_id.partner_invoice_id.id:
                partner_id = self.sale_id.partner_invoice_id.id

        return partner_id
