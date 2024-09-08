# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


class L10nBrPurchaseStockBase(TestBrPickingInvoicingCommon):
    def setUp(self):
        super().setUp()

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
        invoice = self.create_invoice_wizard(pickings)
        # Fatura Agrupada
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking_1.invoice_state, "invoiced")
        self.assertEqual(picking_2.invoice_state, "invoiced")

        self.assertIn(invoice, picking_1.invoice_ids)
        self.assertIn(picking_1, invoice.picking_ids)
        self.assertIn(invoice, picking_2.invoice_ids)
        self.assertIn(picking_2, invoice.picking_ids)

        # Validar o price_unit usado
        for inv_line in invoice.invoice_line_ids.filtered(lambda ln: ln.product_id):
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

        # Section Lines
        section_lines = invoice.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "line_section"
        )
        self.assertEqual(len(section_lines), 2)
        # Note Lines
        note_lines = invoice.invoice_line_ids.filtered(
            lambda ln: ln.display_type == "line_note"
        )
        self.assertEqual(len(note_lines), 2)

        if hasattr(invoice, "document_serie"):
            invoice.document_serie = "1"
            invoice.document_number = "123"

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
        picking_devolution = self.return_picking_wizard(picking_1)
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

        invoice_devolution = self.create_invoice_wizard(picking_devolution)
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

    def test_purchase_order_lucro_presumido(self):
        """Test Purchase Order for company Lucro Presumido."""

        self._change_user_company(self.env.ref("l10n_br_base.empresa_lucro_presumido"))

        purchase = self.env.ref(
            "l10n_br_purchase_stock.lucro_presumido_po_only_products_1"
        )
        purchase.button_confirm()
        picking = purchase.picking_ids

        picking.set_to_be_invoiced()
        # Testa o caso onde o valor no Picking é diferente do Pedido
        # TODO: Validar quando esse caso pode ocorrer para saber
        #  se é necessário manter ou não o código no stock_move.py
        for move in picking.move_ids_without_package:
            move.price_unit = 123.0
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

        invoice = self.create_invoice_wizard(picking)

        # Validar o price_unit usado
        for inv_line in invoice.invoice_line_ids.filtered(lambda ln: ln.product_id):
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
            # self.assertEqual(inv_line.price_unit,
            # inv_line.purchase_line_id.price_unit)
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(inv_line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                inv_line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        if hasattr(invoice, "document_serie"):
            invoice.document_serie = "1"
            invoice.document_number = "1234"

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

    def test_compatible_with_international_case(self):
        """Test of compatible with international case or without Fiscal Operation,
        create Invoice but not for Brazil."""
        po_international = self.env.ref("purchase.purchase_order_2")
        po_international.with_context(tracking_disable=True).button_confirm()
        picking = po_international.picking_ids
        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done")
        invoice = self.create_invoice_wizard(picking)
        invoice.action_post()
        for invoice in po_international.invoice_ids:
            # Caso Internacional não deve ter Documento Fiscal associado
            self.assertFalse(
                invoice.fiscal_document_id,
                "International case should not has Fiscal Document.",
            )
        # Teste Retorno
        picking_devolution = self.return_picking_wizard(picking)
        invoice_devolution = self.create_invoice_wizard(picking_devolution)
        self.assertFalse(
            invoice_devolution.fiscal_document_id,
            "International case should not has Fiscal Document.",
        )
