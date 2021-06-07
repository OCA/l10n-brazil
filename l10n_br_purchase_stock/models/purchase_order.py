# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_create_invoice_policy = fields.Selection(
        selection=[
            ("purchase_order", _("Purchase Order")),
            ("stock_picking", _("Stock Picking")),
        ],
        relation="company_id.purchase_create_invoice_policy",
    )

    @api.model
    def _prepare_picking(self):
        values = super()._prepare_picking()
        values.update(self._prepare_br_fiscal_dict())
        if self.company_id.purchase_create_invoice_policy == "stock_picking":
            values["invoice_state"] = "2binvoiced"

        return values
