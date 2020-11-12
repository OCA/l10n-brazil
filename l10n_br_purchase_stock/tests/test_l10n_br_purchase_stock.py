# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_br_purchase.tests import test_l10n_br_purchase


class L10nBrPurchaseStockBase(test_l10n_br_purchase.L10nBrPurchaseBaseTest):

    def _picking_purchase_order(self, order):
        self.assertEqual(
            order.picking_count, 1,
            'Purchase: one picking should be created"'
        )

        picking = order.picking_ids[0]
        for move_line in picking.move_line_ids:
            move_line.write({'qty_done': move_line.move_id.product_uom_qty})
        picking.with_context(tracking_disable=True).button_validate()
        self.assertEqual(
            order.order_line.mapped('qty_received'), [4.0, 2.0],
            'Purchase: all products should be received"')

    def test_l10n_br_purchase_products(self):
        super().test_l10n_br_purchase_products()
        self._picking_purchase_order(self.po_products)
