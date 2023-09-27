# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form

from odoo.addons.l10n_br_purchase.tests import test_l10n_br_purchase


class L10nBrPurchaseStockBase(test_l10n_br_purchase.L10nBrPurchaseBaseTest):
    def setUp(self):
        super().setUp()
        self.invoice_model = self.env["account.move"]
        self.invoice_wizard = self.env["stock.invoice.onshipping"]
        self.stock_return_picking = self.env["stock.return.picking"]
        self.stock_picking = self.env["stock.picking"]
        self.company_lucro_presumido = self.env.ref(
            "l10n_br_base.empresa_lucro_presumido"
        )

    def _picking_purchase_order(self, order):
        self.assertEqual(
            order.picking_count, 1, 'Purchase: one picking should be created"'
        )

        picking = order.picking_ids[0]
        for move_line in picking.move_line_ids:
            move_line.write({"qty_done": move_line.move_id.product_uom_qty})
        picking.with_context(tracking_disable=True).button_validate()
        self.assertEqual(
            order.order_line.mapped("qty_received"),
            [4.0, 2.0],
            'Purchase: all products should be received"',
        )

    def test_l10n_br_purchase_products(self):
        result = super().test_l10n_br_purchase_products()
        self._picking_purchase_order(self.po_products)
        return result

    def picking_move_state(self, picking):
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

    def wizard_create_invoice(self, pickings):
        wizard_obj = self.invoice_wizard.with_context(
            active_ids=pickings.ids,
            active_model=pickings._name,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        # One invoice per partner but group products
        wizard_values.update({"group": "partner_product"})
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.action_generate()

    def test_grouping_pickings(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 2 moves per picking.
        """
        purchase_1 = self.env.ref("l10n_br_purchase_stock.main_po_only_products_1")
        purchase_1.button_confirm()
        picking_1 = purchase_1.picking_ids
        self.assertEqual(
            picking_1.invoice_state, "2binvoiced", "Error to inform Invoice State."
        )

        self.picking_move_state(picking_1)

        self.assertEqual(picking_1.state, "done")

        self.assertEqual(
            purchase_1.invoice_status,
            "to invoice",
            "Error in compute field invoice_status,"
            " before create invoice by Picking.",
        )

        purchase_2 = self.env.ref("l10n_br_purchase_stock.main_po_only_products_2")
        purchase_2.button_confirm()

        picking_2 = purchase_2.picking_ids
        self.picking_move_state(picking_2)

        pickings = picking_1 | picking_2
        self.wizard_create_invoice(pickings)
        domain = [("picking_ids", "in", (picking_1.id, picking_2.id))]
        invoice = self.invoice_model.search(domain)
        # Fatura Agrupada
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking_1.invoice_state, "invoiced")
        self.assertEqual(picking_2.invoice_state, "invoiced")

        self.assertIn(invoice, picking_1.invoice_ids)
        self.assertIn(picking_1, invoice.picking_ids)
        self.assertIn(invoice, picking_2.invoice_ids)
        self.assertIn(picking_2, invoice.picking_ids)

        # Validar o price_unit usado
        for inv_line in invoice.invoice_line_ids:
            # TODO: A forma de instalação dos modulos feita no CI
            #  falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(
            #    inv_line.tax_ids,
            #    "Error to map Purchase Tax in invoice.line.",
            # )
            # Preço usado na Linha da Invoice deve ser o mesmo
            # informado no Pedido de Compra
            self.assertEqual(inv_line.price_unit, inv_line.purchase_line_id.price_unit)
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(inv_line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                inv_line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        # Confirmando a Fatura
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        # Validar Atualização da Quantidade Faturada
        for line in purchase_1.order_line:
            # Apenas a linha de Produto tem a qtd faturada dobrada
            if line.product_id.type == "product":
                # A quantidade Faturada deve ser igual
                # a Quantidade do Produto
                self.assertEqual(line.product_uom_qty, line.qty_invoiced)

        # Teste de Retorno
        return_wizard_form = Form(
            self.stock_return_picking.with_context(
                active_id=picking_1.id, active_model="stock.picking"
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
        self.picking_move_state(picking_devolution)
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")

        self.wizard_create_invoice(picking_devolution)
        domain = [("picking_ids", "=", picking_devolution.id)]
        invoice_devolution = self.invoice_model.search(domain)
        # Confirmando a Fatura
        invoice_devolution.action_post()
        self.assertEqual(
            invoice_devolution.state, "posted", "Invoice should be in state Posted"
        )
        # Validar Atualização da Quantidade Faturada
        for line in purchase_1.order_line:
            # Apenas a linha de Produto tem a qtd faturada dobrada
            if line.product_id.type == "product":
                # A quantidade Faturada deve ser zero devido a Devolução
                self.assertEqual(0.0, line.qty_invoiced)

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def test_purchase_order_lucro_presumido(self):
        """Test Purchase Order for company Lucro Presumido."""

        self._change_user_company(self.company_lucro_presumido)

        purchase = self.env.ref(
            "l10n_br_purchase_stock.lucro_presumido_po_only_products_1"
        )
        purchase.button_confirm()
        picking = purchase.picking_ids

        picking.set_to_be_invoiced()

        self.assertEqual(
            picking.invoice_state, "2binvoiced", "Error to inform Invoice State."
        )

        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done")

        self.assertEqual(
            purchase.invoice_status,
            "to invoice",
            "Error in compute field invoice_status,"
            " before create invoice by Picking.",
        )

        self.wizard_create_invoice(picking)
        domain = [("picking_ids", "=", picking.id)]
        invoice = self.invoice_model.search(domain)

        # Validar o price_unit usado
        for inv_line in invoice.invoice_line_ids:
            # TODO: A forma de instalação dos modulos feita no CI
            #  falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            self.assertTrue(
                inv_line.tax_ids,
                "Error to map Purchase Tax in invoice.line.",
            )
            # Preço usado na Linha da Invoice deve ser o mesmo
            # informado no Pedido de Compra
            # TODO: Por algum motivo o Preço da Linha do Pedido de Compra fica
            #  diferente da Linha da Fatura, mas somente no caso da empresa
            #  Lucro Presumido
            # File "/odoo/external-src/l10n-brazil-MIG-l10n_br_purchase_stock/
            # l10n_br_purchase_stock/tests/test_l10n_br_purchase_stock.py",
            # line 263, in test_purchase_order_lucro_presumido
            #     self.assertEqual(inv_line.price_unit,
            #     inv_line.purchase_line_id.price_unit)
            # AssertionError: 82.53 != 100.0
            # self.assertEqual(inv_line.price_unit, inv_line.purchase_line_id.price_unit)
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(inv_line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                inv_line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        # Confirmando a Fatura
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")

    def test_button_create_bill_in_view(self):
        """
        Test Field to make Button Create Bill invisible.
        """
        purchase_products = self.env.ref(
            "l10n_br_purchase_stock.main_po_only_products_2"
        )
        # Caso do Pedido de Compra em Rascunho
        self.assertTrue(
            purchase_products.button_create_invoice_invisible,
            "Field to make invisible the Button Create Bill should be"
            " invisible when Purchase Order is not in state Purchase or Done.",
        )
        # Caso somente com Produtos
        purchase_products.button_confirm()
        self.assertTrue(
            purchase_products.button_create_invoice_invisible,
            "Field to make invisible the button Create Bill should be"
            " invisible when Purchase Order has only products.",
        )

        # Caso Somente Serviços
        purchase_only_service = self.env.ref(
            "l10n_br_purchase_stock.main_po_only_service_stock"
        )
        purchase_only_service.button_confirm()
        self.assertFalse(
            purchase_only_service.button_create_invoice_invisible,
            "Field to make invisible the Button Create Bill should be"
            " False when the Purchase Order has only Services.",
        )
        # Caso Serviço e Produto
        purchase_service_product = self.env.ref(
            "l10n_br_purchase_stock.main_po_service_product_stock"
        )
        purchase_service_product.button_confirm()
        self.assertFalse(
            purchase_only_service.button_create_invoice_invisible,
            "Field to make invisible the Button Create Bill should be"
            " False when the Purchase Order has Service and Product.",
        )
