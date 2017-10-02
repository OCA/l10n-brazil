# -*- coding: utf-8 -*-
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests.common import TransactionCase
from datetime import date


class Tests(TransactionCase):

    def setUp(self):
        super(Tests, self).setUp()
        self.partner_normal = self.browse_ref(
            'l10n_br_base.res_partner_cliente1_sp')

        self.product_normal = self.browse_ref(
            'product.product_product_10'
        )
        self.pricelist_model = self.env['product.pricelist']
        self.sale_order_line_model = self.env['sale.order.line']
        self.sale_order_model = self.env['sale.order']
        self.stock_transfer_details = self.registry("stock.transfer_details")
        self.stock_invoice = self.registry("stock.invoice.onshipping")
        self.order_invoice = self.registry("sale.advance.payment.inv")
        self.account_invoice = self.env["account.invoice"]
        default_keys = self.sale_order_model._defaults.keys()
        self.default_vals = self.sale_order_model.default_get(default_keys)
        self.journal_id = self.env.ref('account.sales_journal')
        self.stock_picking_model = self.env['stock.picking']

    def _create_sale_order(self):
        vals = self.default_vals
        vals['order_policy'] = 'picking'
        vals['partner_id'] = self.partner_normal.id
        context = {
            'fiscal_category_id': vals['fiscal_category_id'],
            'company_id': vals['company_id'],
        }

        onchange_partner = self.sale_order_model.with_context(
            context
        ).onchange_partner_id(
            self.partner_normal.id
        )['value']
        self.assertEquals(
            onchange_partner['fiscal_position'],
            self.ref(
                'l10n_br_account_product.'
                'fp_78df616ab31e95ee46c6a519a2ce9e12_internal_demo'
            )
        )

        onchanged_product = self.env['sale.order.line'].product_id_change(
            False,
            self.product_normal.id,
            qty=2,
            uom=self.product_normal.uom_id.id,
            partner_id=self.partner_normal.id,
            fiscal_position=False
        )

        context = {
            'lang': u'pt_BR',
            'parent_fiscal_position': False,
            'tz': 'America/Sao_Paulo',
            'uid': 1,
            'company_id': vals['company_id'],
            'parent_fiscal_category_id': vals['fiscal_category_id'],
            'fiscal_category_id': vals['fiscal_category_id'],
            'partner_invoice_id': self.partner_normal.id,
            'pricelist': 1,
            'field_parent': 'order_id',
            'partner_id': self.partner_normal.id,
            'uom': False,
            'quantity': 2
        }

        product_obj = self.registry('product.product').browse(
            self.cr, self.uid, self.product_normal.id, context=context
        )

        line_values = {
            'fiscal_category_id': vals['fiscal_category_id'],
            'product_id': product_obj.id,
            'product_uom_qty': 2,
            'product_uom': product_obj.uom_id.id,
            'price_unit': product_obj.price,
            'tax_id': [(6, 0, onchanged_product['value']['tax_id'])]
        }

        vals['order_line'] = [(0, 0, line_values)]
        vals.update(onchange_partner)
        vals['name'] = self.registry('ir.sequence').get(
            self.cr, self.uid, 'sale.order', context=None
        ) or '/'

        return self.sale_order_model.create(vals)

    def _create_picking(self, sale_order):
        sale_order.signal_workflow('order_confirm')
        picking = self.stock_picking_model.search(
            [
                ('origin', '=', sale_order.name)
            ]
        )
        return picking

    def _create_invoice_from_picking(self, picking):
        data = picking.force_assign()
        self.assertEqual(picking.state, 'assigned')
        self.assertTrue(data)
        self.run_picking(picking)
        done = picking.action_done()
        self.assertTrue(done)
        self.assertEqual(picking.state, 'done')
        invoice_id = self.run_create_invoice(picking)
        return self.account_invoice.browse(invoice_id)

    def run_picking(self, pick, split=False):
        cr = self.env.cr
        uid = self.env.uid
        context = self.env.context.copy()
        context.update(
            {
                'active_model': 'stock.picking',
                'active_ids': [pick.id],
                'active_id': len([pick.id]) and pick.id or False
            }
        )

        pick_wizard_id = self.stock_transfer_details.create(
            cr, uid, {'picking_id': pick.id}, context)
        pick_wizard = self.stock_transfer_details.browse(
            cr, uid, pick_wizard_id)
        if split:
            pick_wizard.item_ids[0].split_quantities()
            pick_wizard.refresh()
        return self.stock_transfer_details.do_detailed_transfer(
            cr, uid, [pick_wizard_id], context)

    def run_create_invoice(self, pick):
        cr = self.env.cr
        uid = self.env.uid
        context = self.env.context.copy()
        context.update(
            {
                'active_ids': [pick.id],
                'active_id': pick.id,
                'active_model': 'stock.picking',
                'custom_invoice': False,
            }
        )
        inv_wizard_id = self.stock_invoice.create(
            cr, uid,
            {
                'journal_id': self.journal_id[0].id,
                'invoice_date': date.today().strftime('%Y-%m-%d')
            }, context)

        return self.stock_invoice.create_invoice(
            cr, uid, [inv_wizard_id], context)

    def test_sale_order(self):
        """Test creation of sale order"""
        sale_order = self._create_sale_order()

        self.assertEquals(
            71.94,
            sale_order.amount_total,
            "The amount total of the sale order is not correct"
        )

    def test_picking_from_sale_order(self):
        """Test creation of picking from sale order"""
        sale_order = self._create_sale_order()
        picking = self._create_picking(sale_order)
        self.assertTrue(
            picking,
            "Picking from the sale order is not created correctly!"
        )

    def test_create_invoice_from_picking(self):
        """Test creation of invoice from picking"""
        sale_order = self._create_sale_order()
        picking = self._create_picking(sale_order)
        invoice = self._create_invoice_from_picking(picking)

        self.assertTrue(
            invoice,
            "Invoice from picking is not created correctly!"
        )

    def test_sale_order_values_with_invoice_values(self):
        """Compare values between the sale order and the invoice created"""
        sale_order = self._create_sale_order()
        picking = self._create_picking(sale_order)
        invoice = self._create_invoice_from_picking(picking)

        self.assertEqual(
            sale_order.amount_total,
            invoice.amount_total,
            "Invoice created has different amount total from the sale order"
        )
        self.assertEqual(
            len(sale_order.order_line),
            len(invoice.invoice_line),
            "Invoice has different number of lines from the sale order"
        )
        self.assertNotEqual(
            0, invoice.invoice_line.quantity,
            "Quantity of products is 0!"
        )
        self.assertNotEqual(
            0, invoice.invoice_line.price_subtotal,
            "Price of the product in the invoice is 0!"
        )
