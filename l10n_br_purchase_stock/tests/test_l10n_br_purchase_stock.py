# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_br_purchase.tests import test_l10n_br_purchase


class L10nBrPurchaseStockBase(test_l10n_br_purchase.L10nBrPurchaseBaseTest):

    def setUp(self):
        super().setUp()
        self.invoice_model = self.env['account.invoice']
        self.invoice_wizard = self.env['stock.invoice.onshipping']

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

    def test_grouping_pickings(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 2 moves per picking.
        """
        purchase_1 = self.env.ref(
            'l10n_br_purchase_stock.main_po_only_products_1')
        purchase_1.button_confirm()
        picking_1 = purchase_1.picking_ids
        self.assertEqual(picking_1.invoice_state, '2binvoiced',
                         'Error to inform Invoice State.')

        picking_1.action_confirm()
        picking_1.action_assign()
        # Force product availability
        for move in picking_1.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking_1.button_validate()
        self.assertEqual(picking_1.state, 'done')

        self.assertEquals(
            purchase_1.invoice_status, 'to invoice',
            "Error in compute field invoice_status,"
            " before create invoice by Picking."
        )

        purchase_2 = self.env.ref(
            'l10n_br_purchase_stock.main_po_only_products_2')
        purchase_2.button_confirm()
        picking_2 = purchase_2.picking_ids
        picking_2.action_confirm()
        picking_2.action_assign()
        # Force product availability
        for move in picking_2.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking_2.button_validate()

        pickings = picking_1 | picking_2
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update({
            'group': 'partner_product',
        })
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [('picking_ids', 'in', (picking_1.id, picking_2.id))]
        invoice = self.invoice_model.search(domain)
        # Fatura Agrupada
        self.assertEquals(len(invoice), 1)
        self.assertEqual(picking_1.invoice_state, 'invoiced')
        self.assertEqual(picking_2.invoice_state, 'invoiced')

        self.assertIn(invoice, picking_1.invoice_ids)
        self.assertIn(picking_1, invoice.picking_ids)
        self.assertIn(invoice, picking_2.invoice_ids)
        self.assertIn(picking_2, invoice.picking_ids)

        # Validar o price_unit usado
        for inv_line in invoice.invoice_line_ids:
            self.assertTrue(
                inv_line.invoice_line_tax_ids,
                'Error to map Purchase Tax in invoice.line.')
            # Preço usado na Linha da Invoice deve ser o mesmo
            # informado no Pedido de Compra
            self.assertEqual(inv_line.price_unit,
                             inv_line.purchase_line_id.price_unit)
