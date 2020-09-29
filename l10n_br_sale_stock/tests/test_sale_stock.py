# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleStock(TransactionCase):
    def test_02_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return
        of the picking. Check that a refund invoice is well generated.
        """
        # intial so
        self.partner = self.env.ref('l10n_br_base.res_partner_address_ak2')
        self.product = self.env.ref('product.product_delivery_01')
        so_vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 3.0,
                'product_uom': self.product.uom_id.id,
                'price_unit': self.product.list_price
                })],
            'pricelist_id': self.env.ref('product.list0').id,
            }
        self.so = self.env['sale.order'].create(so_vals)

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids,
                        'Sale Stock: no picking created for "invoice on '
                        'delivery" storable products')

        # set stock.picking to be invoiced
        self.assertTrue(len(self.so.picking_ids) == 1,
                       'More than one stock picking for sale.order')
        self.so.picking_ids.set_to_be_invoiced()

        # validate stock.picking
        stock_picking = self.so.picking_ids
        self.env['stock.immediate.transfer'].create(
            {'pick_ids': [(4, stock_picking.id)]}).process()

        # compare sale.order.line with stock.move
        stock_move = stock_picking.move_lines
        sale_order_line = self.so.order_line

        sm_fields = [key for key in self.env['stock.move']._fields.keys()]
        sol_fields = [key for key in self.env[
            'sale.order.line']._fields.keys()]

        skipped_fields = [
            'id',
            'display_name',
            'state',
            ]
        common_fields = list(set(sm_fields) & set(sol_fields) - set(
            skipped_fields))

        for field in common_fields:
            self.assertEqual(stock_move[field],
                             sale_order_line[field],
                             'Field %s failed to transfer from '
                             'sale.order.line to stock.move' % field)

