# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests import SavepointCase


@tagged('post_install', '-at_install')
class TestSaleStock(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.invoice_model = self.env['account.invoice']
        self.invoice_wizard = self.env['stock.invoice.onshipping']
        self.stock_return_picking = self.env['stock.return.picking']
        self.stock_picking = self.env['stock.picking']

        # TODO: Em uma instalção direta do modulo
        #  $ odoo -d test -i l10n_br_sale_stock --stop-after-init
        #  e depois
        #  $ odoo -d test --update=l10n_br_sale_stock --test-enable
        #  o campo do Diário não está vindo preenchido a solução e forçar
        #  preenchimento para não ter erro nos testes porem no caso dos dados
        #  demo ao testar na tela vai continuar o problema, para evita-lo é
        #  preciso instalar o l10n_br_account antes ou preencher manualmente,
        #  porém isso é um problema já que a instalação direta do modulo deve
        #  funcionar sem isso.
        #  No modulo l10n_br_sale para resolver esse problema é feito isso
        #  https://github.com/OCA/l10n-brazil/blob/12.0/l10n_br_sale/
        #  hooks.py#L35 e https://github.com/OCA/l10n-brazil/blob/12.0/
        #  l10n_br_sale/demo/fiscal_operation_simple.xml#L10 mas por algum
        #  motivo não vem carregado aqui, mesmo tendo o l10n_br_sale como
        #  dependencia.
        self.fiscal_operation_venda = self.env.ref('l10n_br_fiscal.fo_venda')
        if not self.fiscal_operation_venda.journal_id:
            self.fiscal_operation_venda.journal_id = \
                self.env.ref('l10n_br_coa_simple.sale_journal_main_company')
        self.fiscal_operation_dev_venda = self.env.ref(
            'l10n_br_fiscal.fo_devolucao_venda')
        if not self.fiscal_operation_dev_venda.journal_id:
            self.fiscal_operation_dev_venda.journal_id = \
                self.env.ref('l10n_br_coa_simple.general_journal_main_company')

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

        for line in self.so.order_line:
            line._onchange_product_id_fiscal()

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids,
                        'Sale Stock: no picking created for "invoice on '
                        'delivery" storable products')

        # set stock.picking to be invoiced
        self.assertTrue(
            len(self.so.picking_ids) == 1, 'More than one stock '
                                           'picking for sale.order')
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

    def test_picking_sale_order_product_and_service(self):
        """
        Test Sale Order with product and service
        """

        sale_order_2 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_2')
        sale_order_2.action_confirm()

        # Metodo de criação da fatura a partir do sale.order
        # deve gerar apenas a linha de serviço
        sale_order_2.action_invoice_create(final=True)
        # Deve existir apenas a Fatura/Documento Fiscal de Serviço
        self.assertEquals(1, sale_order_2.invoice_count)
        for invoice in sale_order_2.invoice_ids:
            for line in invoice.invoice_line_ids:
                self.assertEquals(line.product_id.type, 'service')
            # Confirmando a Fatura de Serviço
            invoice.action_invoice_open()
            self.assertEquals(
                invoice.state, 'open', 'Invoice should be in state Open')

        picking = sale_order_2.picking_ids
        # Check product availability
        picking.action_assign()
        # Apenas o Produto criado
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(picking.invoice_state, '2binvoiced')
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=picking.ids,
            active_model=picking._name,
            active_id=picking.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [('picking_ids', '=', picking.id)]
        invoice = self.invoice_model.search(domain)
        self.assertEqual(picking.invoice_state, 'invoiced')
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        # Picking criado com o Partner Shipping da Sale Order
        self.assertEqual(picking.partner_id, sale_order_2.partner_shipping_id)
        # Fatura criada com o Partner Invoice da Sale Order
        self.assertEqual(invoice.partner_id, sale_order_2.partner_invoice_id)
        # Fatura criada com o Partner Shipping usado no Picking
        self.assertEqual(invoice.partner_shipping_id, picking.partner_id)
        # Quando informado usar o Termo de Pagto definido no Pedido de Venda
        # e não o padrão do cliente
        self.assertEqual(
            invoice.payment_term_id, sale_order_2.payment_term_id)

        # Apenas a Fatura com a linha do produto foi criada
        self.assertEqual(len(invoice.invoice_line_ids), 1)

        # No Pedido de Venda devem existir duas Faturas/Documentos Fiscais
        # de Serviço e Produto
        self.assertEquals(2, sale_order_2.invoice_count)

        # Confirmando a Fatura
        invoice.action_invoice_open()
        self.assertEquals(
            invoice.state, 'open', 'Invoice should be in state Open')

        # Teste de Retorno
        self.return_wizard = self.stock_return_picking.with_context(
            dict(active_id=picking.id)).create(
            dict(invoice_state='2binvoiced'))

        result_wizard = self.return_wizard.create_returns()
        self.assertTrue(result_wizard, 'Create returns wizard fail.')
        picking_devolution = self.stock_picking.browse(
            result_wizard.get('res_id'))

        self.assertEqual(picking_devolution.invoice_state, '2binvoiced')
        self.assertTrue(picking_devolution.fiscal_operation_id,
                        'Missing Fiscal Operation.')
        for line in picking_devolution.move_lines:
            self.assertEqual(line.invoice_state, '2binvoiced')
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(
                line.fiscal_operation_id,
                'Missing Fiscal Operation.')
            self.assertTrue(
                line.fiscal_operation_line_id,
                'Missing Fiscal Operation Line.')
        picking_devolution.action_confirm()
        picking_devolution.action_assign()
        # Force product availability
        for move in picking_devolution.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking_devolution.button_validate()
        self.assertEquals(
            picking_devolution.state, 'done',
            'Change state fail.'
        )
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=picking_devolution.ids,
            active_model=picking_devolution._name,
            active_id=picking_devolution.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [('picking_ids', '=', picking_devolution.id)]
        invoice_devolution = self.invoice_model.search(domain)
        # Confirmando a Fatura
        invoice_devolution.action_invoice_open()
        self.assertEquals(
            invoice_devolution.state, 'open',
            'Invoice should be in state Open')
        # Validar Atualização da Quantidade Faturada
        for line in sale_order_2.order_line:
            # Apenas a linha de Produto tem a qtd faturada dobrada
            if line.product_id.type == 'product':
                # A quantidade Faturada deve ser duas vezes
                # a quantidade do Produto já que foram criadas
                # duas Faturas a de Envio e a de Devolução
                self.assertEqual((2 * line.product_uom_qty), line.qty_invoiced)

    def test_picking_invoicing_partner_shipping_invoiced(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking, but Partner to Shipping is
        different from Partner to Invoice.
        """
        sale_order_1 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_1')
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_2 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_2')
        sale_order_2.action_confirm()
        picking2 = sale_order_2.picking_ids
        # Check product availability
        picking2.action_assign()
        # Force product availability
        for move in picking2.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking2.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking2.state, 'done')
        pickings = picking | picking2
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
        domain = [('picking_ids', 'in', (picking.id, picking2.id))]
        invoice = self.invoice_model.search(domain)
        # Fatura Agrupada
        self.assertEquals(len(invoice), 1)
        self.assertEqual(picking.invoice_state, 'invoiced')
        self.assertEqual(picking2.invoice_state, 'invoiced')
        # Fatura deverá ser criada com o partner_invoice_id
        self.assertEqual(
            invoice.partner_id, sale_order_1.partner_invoice_id)
        # Fatura com o partner shipping
        self.assertEqual(
            invoice.partner_shipping_id, picking.partner_id)
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(invoice, picking2.invoice_ids)
        self.assertIn(picking2, invoice.picking_ids)

        # Not grouping products with different sale line,
        # 3 products from sale_order_1 and 1 product from sale_order_2
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        for inv_line in invoice.invoice_line_ids:
            self.assertTrue(
                inv_line.invoice_line_tax_ids,
                'Error to map Sale Tax in invoice.line.')
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(
                inv_line.fiscal_operation_id,
                'Missing Fiscal Operation.')
            self.assertTrue(
                inv_line.fiscal_operation_line_id,
                'Missing Fiscal Operation Line.')

    def test_ungrouping_pickings_partner_shipping_different(self):
        """
        Test the invoice generation grouped by partner/product with 3
        picking and 3 moves per picking, the 3 has the same Partner to
        Invoice but one has Partner to Shipping so shouldn't be grouping.
        """

        sale_order_1 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_1')
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_3 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_3')
        sale_order_3.action_confirm()
        picking3 = sale_order_3.picking_ids
        # Check product availability
        picking3.action_assign()
        # Force product availability
        for move in picking3.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking3.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking3.state, 'done')

        sale_order_4 = self.env.ref(
            'l10n_br_sale_stock.main_so_l10n_br_sale_stock_4')
        sale_order_4.action_confirm()
        picking4 = sale_order_4.picking_ids
        # Check product availability
        picking4.action_assign()
        # Force product availability
        for move in picking4.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking4.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking3.state, 'done')

        pickings = picking | picking3 | picking4
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
        domain = [(
            'picking_ids', 'in', (picking.id, picking3.id, picking4.id))]
        invoices = self.invoice_model.search(domain)
        # Mesmo tendo o mesmo Partner Invoice se não tiver o
        # mesmo Partner Shipping não deve ser Agrupado
        self.assertEquals(len(invoices), 2)
        self.assertEqual(picking.invoice_state, 'invoiced')
        self.assertEqual(picking3.invoice_state, 'invoiced')
        self.assertEqual(picking4.invoice_state, 'invoiced')

        # Fatura que tem um Partner shipping
        # diferente não foi agrupada
        invoice_pick_1 = invoices.filtered(
            lambda t: t.partner_shipping_id == picking.partner_id)
        # Fatura deverá ser criada com o partner_invoice_id
        self.assertEqual(
            invoice_pick_1.partner_id, sale_order_1.partner_invoice_id)
        # Fatura criada com o Partner Shipping usado no Picking
        self.assertEqual(
            invoice_pick_1.partner_shipping_id, picking.partner_id)

        # Fatura Agrupada, não deve ter o partner_shipping_id preenchido
        invoice_pick_3_4 = invoices.filtered(
            lambda t: not t.partner_shipping_id)
        self.assertIn(invoice_pick_3_4, picking3.invoice_ids)
        self.assertIn(invoice_pick_3_4, picking4.invoice_ids)
