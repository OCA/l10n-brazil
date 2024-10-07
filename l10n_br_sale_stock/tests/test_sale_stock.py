# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# TODO: In v16 check the possiblity to use the commom.py
# from stock_picking_invoicing
# https://github.com/OCA/account-invoicing/blob/16.0/
# stock_picking_invoicing/tests/common.py
from odoo import exceptions
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_stock_account.tests.common import TestBrPickingInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleStock(TestBrPickingInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Problem in sale_stock_picking_invoicing
        # In order to avoid errors in the tests CI environment when the tests
        # Create of Invoice by Sale Order using sale.advance.payment.inv object
        # is necessary let default policy as sale_order, just affect demo data.
        # TODO: Is there other form to avoid this problem?
        # cls.companies = cls.env["res.company"].search(
        #    [("sale_invoicing_policy", "=", "sale_order")]
        # )
        # for company in cls.companies:
        #    company.sale_invoicing_policy = "stock_picking"

    def set_sale_invoicing_policy(self):
        # Isso deveria estar sendo feito no setupUpClass mas retorna erro:
        # l10n_br_sale_stock/tests/test_sale_stock.py", line 53, in setUpClass
        # cls.companies = cls.env["res.company"].search(
        # AttributeError: type object 'TestSaleStock' has no attribute 'env'
        # TODO: Na v16 isso não parece acontecer, pode ser algo referente ao ORM,
        #  ver na migração
        self.companies = self.env["res.company"].search(
            [("sale_invoicing_policy", "=", "sale_order")]
        )
        for company in self.companies:
            company.sale_invoicing_policy = "stock_picking"

    def test_02_sale_stock_return(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice
        the SO, then do a return
        of the picking. Check that a refund invoice is well generated.
        """
        # intial so
        self.set_sale_invoicing_policy()
        self.partner = self.env.ref("l10n_br_base.res_partner_address_ak2")
        self.product = self.env.ref("product.product_delivery_01")

        sale_form = Form(self.env["sale.order"])
        sale_form.partner_id = self.partner
        sale_form.pricelist_id = self.env.ref("product.list0")
        sale_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        with sale_form.order_line.new() as line:
            line.name = self.product.name
            line.product_id = self.product
            line.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
            line.product_uom_qty = 3

        self.so = sale_form.save()

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
        self.set_sale_invoicing_policy()
        sale_order_2 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_2")
        sale_order_form = Form(sale_order_2)
        sale_order = sale_order_form.save()
        sale_order.action_confirm()
        # Metodo de criação da fatura a partir do sale.order
        # deve gerar apenas a linha de serviço
        sale_order._create_invoices(final=True)
        # Deve existir apenas a Fatura/Documento Fiscal de Serviço
        self.assertEqual(1, sale_order.invoice_count)
        for invoice in sale_order.invoice_ids:
            for line in invoice.invoice_line_ids.filtered(lambda ln: ln.product_id):
                self.assertEqual(line.product_id.type, "service")
            # Confirmando a Fatura de Serviço
            invoice.action_post()
            self.assertEqual(
                invoice.state, "posted", "Invoice should be in state Posted."
            )

        picking = sale_order.picking_ids
        # Apenas o Produto criado
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(picking.invoice_state, "2binvoiced")
        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done")
        invoice = self.create_invoice_wizard(picking)
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
        self.assertEqual(
            len(invoice.invoice_line_ids.filtered(lambda ln: ln.product_id)), 1
        )

        # No Pedido de Venda devem existir duas Faturas/Documentos Fiscais
        # de Serviço e Produto
        self.assertEqual(2, sale_order_2.invoice_count)

        # Confirmando a Fatura
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted.")

        sale_order_line = sale_order.order_line.filtered(
            lambda ln: ln.product_id.type == "product"
        )

        # Validar Atualização da Quantidade Faturada
        # A quantidade Faturada deve ser igual a Quantidade do Produto
        self.assertEqual(sale_order_line.product_uom_qty, sale_order_line.qty_invoiced)

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
            # Field sequence add in creation of Invoice
            "sequence",
        ]

        common_fields = list(set(acl_fields) & set(sol_fields) - set(skipped_fields))
        invoice_lines = picking.invoice_ids.invoice_line_ids.filtered(
            lambda ln: ln.product_id == sale_order_line.product_id
        )

        for field in common_fields:
            self.assertEqual(
                sale_order_line[field],
                invoice_lines[field],
                "Field %s failed to transfer from "
                "sale.order.line to account.move.line" % field,
            )

        for inv_line in invoice_lines.filtered(
            lambda ln: ln.product_id == sale_order_line.product_id
        ):
            self.assertEqual(sale_order_line.product_uom, inv_line.product_uom_id)

        # Teste de Retorno
        picking_devolution = self.return_picking_wizard(picking)

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
            invoice_devolution.state, "posted", "Invoice should be in state Posted."
        )
        # Validar Atualização da Quantidade Faturada
        # A quantidade Faturada deve ser zero devido a Devolução
        self.assertEqual(0.0, sale_order_line.qty_invoiced)

    def test_picking_invoicing_partner_shipping_invoiced(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking, but Partner to Shipping is
        different from Partner to Invoice.
        """
        self.set_sale_invoicing_policy()
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_1")
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        self.picking_move_state(picking)

        sale_order_2 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_2")
        sale_order_2.action_confirm()
        picking2 = sale_order_2.picking_ids

        self.picking_move_state(picking2)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking2.state, "done")
        pickings = picking | picking2
        invoice = self.create_invoice_wizard(pickings)

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
        # sale_order_1 | 3 products           | 1 Note | 1 Section
        # sale_order_2 | 1 product -1 service | 1 Note | 1 Section |
        len_sale_lines = len(sale_order_1.order_line) + (
            len(sale_order_2.order_line) - 1
        )

        self.assertEqual(len(invoice.invoice_line_ids), len_sale_lines)
        for inv_line in invoice.invoice_line_ids.filtered(lambda ln: ln.product_id):
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
        self.set_sale_invoicing_policy()
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_1")
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        self.picking_move_state(picking)

        sale_order_3 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_3")
        sale_order_3.action_confirm()
        picking3 = sale_order_3.picking_ids
        self.picking_move_state(picking3)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        sale_order_4 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_4")
        sale_order_4.action_confirm()
        picking4 = sale_order_4.picking_ids
        self.picking_move_state(picking4)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking3.state, "done")

        pickings = picking | picking3 | picking4
        invoices = self.create_invoice_wizard(pickings)

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

        # TODO: O processo de criação a partir de um Pedido de Venda vem
        #  preenchido o campo partner_shipping_id, isso deve ser mantido por
        #  ser considerado o padrão ou é melhor remover o partner_shipping_id
        #  quando o valor é igual ao partner_id?

        # Fatura Agrupada, não deve ter o partner_shipping_id preenchido
        # invoice_pick_3_4 = invoices.filtered(lambda t: not t.partner_shipping_id)

        invoice_pick_3_4 = invoices.filtered(
            lambda t: t.partner_shipping_id == t.partner_id
        )
        self.assertIn(invoice_pick_3_4, picking3.invoice_ids)
        self.assertIn(invoice_pick_3_4, picking4.invoice_ids)

    def test_synchronize_sale_partner_shipping_in_stock_picking(self):
        """
        Test the synchronize Sale Partner Shipping in Stock Picking
        """
        self.set_sale_invoicing_policy()
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_1")
        sale_order_1.action_confirm()
        picking = sale_order_1.picking_ids
        sale_order_1.partner_shipping_id = self.env.ref(
            "l10n_br_base.res_partner_address_ak2"
        ).id
        sale_order_1._onchange_partner_shipping_id()
        self.assertEqual(sale_order_1.partner_shipping_id, picking.partner_id)

    def test_lucro_presumido_company(self):
        """
        Test Lucro Presumido Company
        """
        self.set_sale_invoicing_policy()
        self._change_user_company(self.env.ref("l10n_br_base.empresa_lucro_presumido"))
        sale_order_1 = self.env.ref("l10n_br_sale_stock.lucro_presumido-sale_order_1")
        sale_order_form = Form(sale_order_1)
        sale_order = sale_order_form.save()
        sale_order.incoterm = self.env.ref("account.incoterm_FOB")

        sale_order.action_confirm()
        picking = sale_order_1.picking_ids
        self.picking_move_state(picking)
        invoice = self.create_invoice_wizard(picking)
        self.assertEqual(len(invoice), 1)
        for inv_line in invoice.invoice_line_ids.filtered(lambda ln: ln.product_id):
            # TODO: No Travis quando a empresa main_company falha esse browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido ou quando é
            #  feito o teste apenas instalando os modulos l10n_br_account e em
            #  seguida o l10n_br_stock_account.
            self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")

    def test_compatible_with_international_case(self):
        """
        Test compatibility with international cases or
        without Fiscal Operation.
        """
        self.set_sale_invoicing_policy()
        so_international = self.env.ref("sale.sale_order_3")
        so_international.fiscal_operation_id = False
        so_international.action_confirm()
        picking = so_international.picking_ids
        self.picking_move_state(picking)
        invoice = self.create_invoice_wizard(picking)
        invoice.action_post()
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

    def test_form_stock_picking(self):
        """Test Stock Picking with Form"""
        self.set_sale_invoicing_policy()
        sale_order = self.env.ref("l10n_br_sale_stock.main_company-sale_order_1")
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking_form = Form(picking)
        # Testa o mapeamento do _get_fiscal_partner
        picking_form.partner_id = self.env.ref("l10n_br_base.res_partner_akretion")
        picking_form.partner_id = self.env.ref("l10n_br_base.res_partner_address_ak3")
        # Apesar do metodo onchange retornar uma OP Fiscal padrão,
        # quando existe um Pedido de Venda associado deve usar retornar
        # a mesma OP Fiscal do Pedido.
        picking_form.invoice_state = "none"
        picking_form.invoice_state = "2binvoiced"
        self.assertEqual(sale_order.fiscal_operation_id, picking.fiscal_operation_id)
        picking_form.save()

    def test_down_payment(self):
        """Test the case with Down Payment"""
        self.set_sale_invoicing_policy()
        sale_order_1 = self.env.ref("l10n_br_sale_stock.main_company-sale_order_1")
        sale_order_1.action_confirm()
        # Create Invoice Sale
        context = {
            "active_model": "sale.order",
            "active_id": sale_order_1.id,
            "active_ids": sale_order_1.ids,
        }
        # Test Create Invoice Policy
        payment = (
            self.env["sale.advance.payment.inv"]
            .with_context(context)
            .create(
                {
                    "advance_payment_method": "delivered",
                }
            )
        )
        with self.assertRaises(exceptions.UserError):
            payment.with_context(context).create_invoices()

        # DownPayment
        payment_wizard = (
            self.env["sale.advance.payment.inv"]
            .with_context(context)
            .create(
                {
                    "advance_payment_method": "percentage",
                    "amount": 50,
                }
            )
        )
        payment_wizard.create_invoices()

        invoice_down_payment = sale_order_1.invoice_ids[0]
        invoice_down_payment.action_post()
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=invoice_down_payment.ids,
            )
        )
        journal_cash = self.env["account.journal"].search(
            [
                ("type", "=", "cash"),
                ("company_id", "=", invoice_down_payment.company_id.id),
            ],
            limit=1,
        )
        payment_register.journal_id = journal_cash
        payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        payment_register.payment_method_id = payment_method_manual_in
        payment_register.amount = invoice_down_payment.amount_total
        payment_register.save()._create_payments()

        picking = sale_order_1.picking_ids
        self.picking_move_state(picking)
        invoice = self.create_invoice_wizard(picking)
        # 3 Products, 1 Section, 1 Note, 1 Down Payment and 1 Section
        # of DownPayment added during the creation of Invoice
        sale_lines = len(sale_order_1.order_line) + 1
        self.assertEqual(len(invoice.invoice_line_ids), sale_lines)
        line_section = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "line_section"
        )
        assert line_section, "Invoice without Line Section for Down Payment."
        down_payment_line = invoice.invoice_line_ids.filtered(
            lambda line: line.sale_line_ids.is_downpayment
        )
        assert down_payment_line, "Invoice without Down Payment line."
        invoice.action_post()
