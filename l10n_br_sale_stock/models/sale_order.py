# Copyright (C) 2020  Magno Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, values):
        """
        When partner_shipping_id is changed after the order is confirmed,
        the related stock.picking records keep the old partner_id, which is
        wrong. In the Brazilian localization, where invoices can be created
        from stock.picking, this can cause errors. So we force the update of
        the partner_id on the related pickings.

        In Odoo 17.0, the native sale_stock module only schedules a warning
        activity but does not update the picking partner.
        """
        if values.get("partner_shipping_id"):
            new_partner_id = values["partner_shipping_id"]
            for record in self:
                pickings = record.picking_ids.filtered(
                    lambda p: (
                        p.state not in ["done", "cancel"]
                        and p.partner_id.id != new_partner_id
                    )
                )
                pickings.write({"partner_id": new_partner_id})

        return super().write(values)
