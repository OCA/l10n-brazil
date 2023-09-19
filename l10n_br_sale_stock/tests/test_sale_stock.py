# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestSaleStock(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice_model = cls.env["account.move"]
        cls.invoice_wizard = cls.env["stock.invoice.onshipping"]
        cls.stock_return_picking = cls.env["stock.return.picking"]
        cls.stock_picking = cls.env["stock.picking"]

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
        cls.fiscal_operation_venda = cls.env.ref("l10n_br_fiscal.fo_venda")
        if not cls.fiscal_operation_venda.journal_id:
            cls.fiscal_operation_venda.journal_id = cls.env.ref(
                "l10n_br_coa_simple.sale_journal_main_company"
            )
        cls.fiscal_operation_dev_venda = cls.env.ref(
            "l10n_br_fiscal.fo_devolucao_venda"
        )
        if not cls.fiscal_operation_dev_venda.journal_id:
            cls.fiscal_operation_dev_venda.journal_id = cls.env.ref(
                "l10n_br_coa_simple.general_journal_main_company"
            )

            cls.stock_picking_sp_lp = cls.env.ref(
                "l10n_br_stock_account.demo_l10n_br_stock_account-picking-1"
            )

        cls.company_lucro_presumido = cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido"
        )

    def test_02_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return
        of the picking. Check that a refund invoice is well generated.
        """
        # intial so
        self.partner = self.env.ref("l10n_br_base.res_partner_address_ak2")
        self.product = self.env.ref("product.product_delivery_01")
        so_vals = {
            "partner_id": self.partner.id,
            "partner_invoice_id": self.partner.id,
            "partner_shipping_id": self.partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": self.product.name,
                        "product_id": self.product.id,
                        "product_uom_qty": 3.0,
                        "product_uom": self.product.uom_id.id,
                        "price_unit": self.product.list_price,
                    },
                )
            ],
            "pricelist_id": self.env.ref("product.list0").id,
        }
        self.so = self.env["sale.order"].create(so_vals)

        for line in self.so.order_line:
            line._onchange_product_id_fiscal()

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(
            self.so.picking_ids,
            'Sale Stock: no picking created for "invoice on '
            'delivery" storable products',
        )

        # set stock.picking to be invoiced
        self.assertTrue(
            len(self.so.picking_ids) == 1,
            "More than one stock " "picking for sale.order",
        )
        self.so.picking_ids.set_to_be_invoiced()

        # validate stock.picking
        stock_picking = self.so.picking_ids

        # compare sale.order.line with stock.move
        stock_move = stock_picking.move_lines
        sale_order_line = self.so.order_line

        sm_fields = [key for key in self.env["stock.move"]._fields.keys()]
        sol_fields = [key for key in self.env["sale.order.line"]._fields.keys()]

        skipped_fields = [
            "id",
            "display_name",
            "state",
        ]
        common_fields = list(set(sm_fields) & set(sol_fields) - set(skipped_fields))

        for field in common_fields:
            self.assertEqual(
                stock_move[field],
                sale_order_line[field],
                "Field %s failed to transfer from "
                "sale.order.line to stock.move" % field,
            )

        self.env["stock.immediate.transfer"].create(
            {"pick_ids": [(4, stock_picking.id)]}
        ).process()

        # O valor do price_unit da stock.move é alterado ao Confirmar o
        # stock.picking de acordo com a forma de valorização de estoque
        # definida( ex.: metodo _run_fifo é chamado e altera o valor do
        # price_unit https://github.com/odoo/odoo/blob/12.0/addons
        # /stock_account/models/stock.py#L255 ), por isso os campos
        # relacionados a esse valor não são iguais.
        # O teste está sendo feito novamente para essa questão ficar clara
        # em alterações e migrações.
        skipped_fields_after_confirm = [
            "price_gross",
            "amount_taxed",
            "financial_total",
            "financial_total_gross",
            "fiscal_price",
            "amount_fiscal",
            "price_unit",
            "amount_untaxed",
            "amount_total",
        ]
        skipped_fields[len(skipped_fields) :] = skipped_fields_after_confirm

        common_fields = list(set(sm_fields) & set(sol_fields) - set(skipped_fields))

        for field in common_fields:
            self.assertEqual(
                stock_move[field],
                sale_order_line[field],
                "Field %s failed to transfer from "
                "sale.order.line to stock.move" % field,
            )

    def test_picking_sale_order_product_and_service(self):
        """
        Test Sale Order with product and service
        """

        sale_order_2 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_2")
        sale_order_2.action_confirm()

        # Forma encontrada para chamar o metodo
        # _compute_get_button_create_invoice_invisible
        sale_order_form = Form(sale_order_2)
        sale_order = sale_order_form.save()
        # Metodo de criação da fatura a partir do sale.order
        # deve gerar apenas a linha de serviço
        sale_order._create_invoices(final=True)
        # Deve existir apenas a Fatura/Documento Fiscal de Serviço
        self.assertEqual(1, sale_order.invoice_count)
        for invoice in sale_order.invoice_ids:
            for line in invoice.invoice_line_ids:
                self.assertEqual(line.product_id.type, "service")
            # Confirmando a Fatura de Serviço
            invoice.action_post()
            self.assertEqual(
                invoice.state, "posted", "Invoice should be in state Posted."
            )

        picking = sale_order.picking_ids
        # Check product availability
        picking.action_assign()
        # Apenas o Produto criado
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(picking.invoice_state, "2binvoiced")
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
            # Usado para validar a transferencia dos campos da linha
            # do Pedido de Venda para a linha da Fatura/Invoice
            sale_order_line = move.sale_line_id
            self.assertEqual(sale_order_line.product_uom, move.product_uom)

        picking.button_validate()
        self.assertEqual(picking.state, "done")
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
        domain = [("picking_ids", "=", picking.id)]
        invoice = self.invoice_model.search(domain)
        self.assertEqual(picking.invoice_state, "invoiced")
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
        self.assertEqual(invoice.invoice_payment_term_id, sale_order_2.payment_term_id)

        # Apenas a Fatura com a linha do produto foi criada
        self.assertEqual(len(invoice.invoice_line_ids), 1)

        # No Pedido de Venda devem existir duas Faturas/Documentos Fiscais
        # de Serviço e Produto
        self.assertEqual(2, sale_order_2.invoice_count)

        # Confirmando a Fatura
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted.")

        # Validar Atualização da Quantidade Faturada
        for line in sale_order_2.order_line:
            # Apenas a linha de Produto tem a qtd faturada dobrada
            if line.product_id.type == "product":
                # A quantidade Faturada deve ser igual
                # a Quantidade do Produto
                self.assertEqual(line.product_uom_qty, line.qty_invoiced)

        # Checar se os campos das linhas do Pedido de Vendas
        # estão iguais as linhas da Fatura/Invoice.
        sol_fields = [key for key in self.env["sale.order.line"]._fields.keys()]

        acl_fields = [key for key in self.env["account.move.line"]._fields.keys()]

        skipped_fields = [
            "agent_ids",
            "id",
            "display_name",
            "state",
            "create_date",
            # O campo da Unidade de Medida possui um nome diferente na
            # account.move.line product_uom_id, por isso é removido porém
            # a copia entre os objetos é testada tanto no stock.move acima
            # quanto na account.move.line abaixo
            "uom_id",
        ]

        common_fields = list(set(acl_fields) & set(sol_fields) - set(skipped_fields))
        invoice_lines = picking.invoice_ids.invoice_line_ids

        for field in common_fields:
            self.assertEqual(
                sale_order_line[field],
                invoice_lines[field],
                "Field %s failed to transfer from "
                "sale.order.line to account.move.line" % field,
            )

        for inv_line in invoice_lines:
            if inv_line.product_id == sale_order_line.product_id:
                self.assertEqual(sale_order_line.product_uom, inv_line.product_uom_id)

        # Teste de Retorno
        return_wizard_form = Form(
            self.stock_return_picking.with_context(
                active_id=picking.id, active_model="stock.picking"
            )
        )
        return_wizard_form.invoice_state = "2binvoiced"
        self.return_wizard = return_wizard_form.save()
        result_wizard = self.return_wizard.create_returns()

        self.assertTrue(result_wizard, "Create returns wizard fail.")
        picking_devolution = self.stock_picking.browse(result_wizard.get("res_id"))

        self.assertEqual(picking_devolution.invoice_state, "2binvoiced")
        self.assertTrue(
            picking_devolution.fiscal_operation_id, "Missing Fiscal Operation."
        )
        for line in picking_devolution.move_lines:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )
        picking_devolution.action_confirm()
        picking_devolution.action_assign()
        # Force product availability
        for move in picking_devolution.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking_devolution.button_validate()
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")
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
        domain = [("picking_ids", "=", picking_devolution.id)]
        invoice_devolution = self.invoice_model.search(domain)
        # Confirmando a Fatura
        invoice_devolution.action_post()
        self.assertEqual(
            invoice_devolution.state, "posted", "Invoice should be in state Posted."
        )
        # Validar Atualização da Quantidade Faturada
        for line in sale_order_2.order_line:
            # Apenas a linha de Produto tem a qtd faturada dobrada
            if line.product_id.type == "product":
                # A quantidade Faturada deve ser zero
                # devido a Devolução
                self.assertEqual(0.0, line.qty_invoiced)

    def test_picking_invoicing_partner_shipping_invoiced(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking, but Partner to Shipping is
        different from Partner to Invoice.
        """
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_1")
        sale_order_1.action_confirm()
        # Forma encontrada para chamar o metodo
        # _compute_get_button_create_invoice_invisible
        sale_order_form = Form(sale_order_1)
        sale_order = sale_order_form.save()
        picking = sale_order.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_2 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_2")
        sale_order_2.action_confirm()
        picking2 = sale_order_2.picking_ids
        # Check product availability
        picking2.action_assign()
        # Force product availability
        for move in picking2.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking2.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking2.state, "done")
        pickings = picking | picking2
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update(
            {
                "group": "partner_product",
            }
        )
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", (picking.id, picking2.id))]
        invoice = self.invoice_model.search(domain)
        # Fatura Agrupada
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")
        # Fatura deverá ser criada com o partner_invoice_id
        self.assertEqual(invoice.partner_id, sale_order_1.partner_invoice_id)
        # Fatura com o partner shipping
        self.assertEqual(invoice.partner_shipping_id, picking.partner_id)
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(invoice, picking2.invoice_ids)
        self.assertIn(picking2, invoice.picking_ids)

        # Not grouping products with different sale line,
        # 3 products from sale_order_1 and 1 product from sale_order_2
        self.assertEqual(len(invoice.invoice_line_ids), 4)
        for inv_line in invoice.invoice_line_ids:
            # TODO: No travis falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(
            #    inv_line.tax_ids, "Error to map Sale Tax in invoice.line."
            # )
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(inv_line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                inv_line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

    def test_ungrouping_pickings_partner_shipping_different(self):
        """
        Test the invoice generation grouped by partner/product with 3
        picking and 3 moves per picking, the 3 has the same Partner to
        Invoice but one has Partner to Shipping so shouldn't be grouping.
        """

        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_1")
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        sale_order_3 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_3")
        sale_order_3.action_confirm()
        picking3 = sale_order_3.picking_ids
        # Check product availability
        picking3.action_assign()
        # Force product availability
        for move in picking3.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking3.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        sale_order_4 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_4")
        sale_order_4.action_confirm()
        picking4 = sale_order_4.picking_ids
        # Check product availability
        picking4.action_assign()
        # Force product availability
        for move in picking4.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking4.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        pickings = picking | picking3 | picking4
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update(
            {
                "group": "partner_product",
            }
        )
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "in", (picking.id, picking3.id, picking4.id))]
        invoices = self.invoice_model.search(domain)
        # Mesmo tendo o mesmo Partner Invoice se não tiver o
        # mesmo Partner Shipping não deve ser Agrupado
        self.assertEqual(len(invoices), 2)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking3.invoice_state, "invoiced")
        self.assertEqual(picking4.invoice_state, "invoiced")

        # Fatura que tem um Partner shipping
        # diferente não foi agrupada
        invoice_pick_1 = invoices.filtered(
            lambda t: t.partner_shipping_id == picking.partner_id
        )
        # Fatura deverá ser criada com o partner_invoice_id
        self.assertEqual(invoice_pick_1.partner_id, sale_order_1.partner_invoice_id)
        # Fatura criada com o Partner Shipping usado no Picking
        self.assertEqual(invoice_pick_1.partner_shipping_id, picking.partner_id)
        # Fatura Agrupada, não deve ter o partner_shipping_id preenchido
        invoice_pick_3_4 = invoices.filtered(lambda t: not t.partner_shipping_id)
        self.assertIn(invoice_pick_3_4, picking3.invoice_ids)
        self.assertIn(invoice_pick_3_4, picking4.invoice_ids)

    def test_synchronize_sale_partner_shipping_in_stock_picking(self):
        """
        Test the synchronize Sale Partner Shipping in Stock Picking
        """
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_so_l10n_br_sale_stock_1")
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        sale_order_1.partner_shipping_id = self.env.ref(
            "l10n_br_base.res_partner_address_ak2"
        ).id
        sale_order_1._onchange_partner_shipping_id()
        self.assertEqual(sale_order_1.partner_shipping_id, picking.partner_id)

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def test_lucro_presumido_company(self):
        """
        Test Lucro Presumido Company
        """
        self._change_user_company(self.company_lucro_presumido)
        sale_order_1 = self.env.ref(
            "l10n_br_sale_stock.l10n_br_sale_stock_lucro_presumido"
        )
        # Forma encontrada para chamar o metodo
        # _compute_get_button_create_invoice_invisible
        # TODO: No travis está retornando um Warning
        #  relacionado ao sale_invoice_plan
        #  WARNING db odoo.models: 'tree_view_ref' requires a
        #  fully-qualified external id (got: 'view_sale_invoice_plan_tree'
        #  for model sale.invoice.plan). Please use the complete `module.view_id`
        #  form instead.
        sale_order_form = Form(sale_order_1)
        sale_order = sale_order_form.save()
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

        wizard_obj = self.invoice_wizard.with_context(
            active_ids=picking.ids,
            active_model=picking._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update(
            {
                "group": "partner_product",
            }
        )
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()
        domain = [("picking_ids", "=", picking.id)]
        invoice = self.invoice_model.search(domain)
        self.assertEqual(len(invoice), 1)
        for inv_line in invoice.invoice_line_ids:
            # TODO: No Travis quando a empresa main_company falha esse browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido ou quando é
            #  feito o teste apenas instalando os modulos l10n_br_account e em
            #  seguida o l10n_br_stock_account.
            self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")
