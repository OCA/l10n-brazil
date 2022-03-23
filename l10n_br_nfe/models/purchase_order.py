# Copyright 2022 KMEE (Renan Hiroki Bastos <renan.hiroki@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.multi
    def _add_supplier_to_product(self):
        res = super(PurchaseOrder, self)._add_supplier_to_product()
        for line in self.order_line:
            product_id = line.product_id
            supplierinfo = product_id.seller_ids.filtered(lambda s: s.name == self.partner_id)[0]
            if supplierinfo and not supplierinfo.product_id:
                product_id.write({'seller_ids': [(1, supplierinfo.id, {'product_id': product_id.id})]})
        return res
