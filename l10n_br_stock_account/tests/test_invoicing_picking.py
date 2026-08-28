# Copyright (C) 2019-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_pck_backorder,
)

from .common import TestBrPickingInvoicingCommon


class InvoicingPickingTest(TestBrPickingInvoicingCommon):
    """Test invoicing picking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_invoicing_picking(self):
        """Test Invoicing Picking"""
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        self.picking_move_state(picking)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.check_br_invoice_created(invoice, picking)
        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        picking_devolution = self.run_picking_devolution(picking)
        invoice_devolution = create_with_form_inv_onshipping(
            self.env, picking_devolution
        )
        self.check_br_invoice_created(invoice_devolution, picking_devolution)

    def test_02_picking_invoicing_by_product2(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking.
        We use same partner for 2 picking so we should have 1 invoice with 3
        lines (and qty 2)
        :return:
        """
        nb_invoice_before = self.env["account.move"].search_count([])
        self.env["account.move"].search_count([])
        picking_1 = self.picking_out_br_1
        self.picking_move_state(picking_1)
        picking_2 = self.picking_out_br_2
        self.picking_move_state(picking_2)
        self.assertEqual(picking_1.state, "done")
        self.assertEqual(picking_2.state, "done")
        invoice = create_with_form_inv_onshipping(self.env, picking_1 | picking_2)
        self.assertEqual(len(invoice), 1)
        self.check_br_invoice_created(invoice, picking_1 | picking_2)
        for inv_line in invoice.invoice_line_ids:
            # qty = 4 because 2 for each stock.move
            self.assertEqual(inv_line.quantity, 4)

        # Now test behaviour if the invoice is delete
        invoice.unlink()
        pickings = picking_1 | picking_2
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.env["account.move"].search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_03_picking_invoicing_by_product3(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking, but 1 picking are the one
        address of the other partner so we should have 2 invoicies
        with 3 lines (and qty 2)
        :return:
        """
        self.env["account.move"].search_count([])
        picking_1 = self.picking_out_br_3
        self.picking_move_state(picking_1)
        picking_2 = self.picking_out_br_4
        self.picking_move_state(picking_2)
        self.assertEqual(picking_1.state, "done")
        self.assertEqual(picking_2.state, "done")
        invoicies = create_with_form_inv_onshipping(self.env, picking_1 | picking_2)
        self.assertEqual(len(invoicies), 2)
        self.assertEqual(picking_1.invoice_state, "invoiced")
        self.assertEqual(picking_2.invoice_state, "invoiced")
        invoice_pick_1 = invoicies.filtered(
            lambda t: t.partner_shipping_id == picking_1.partner_id
        )
        #  Nesse caso está trazendo o mesmo Partner apesar de ser um endereço
        #  de outro principal, isso acontece porque o metodo address_get chamado
        #  pelo get_invoice_partner traz o primeiro res.partner que tem o campo
        #  company_type definido como Company/empresa então para funcionar o caso
        #  de Endereço de Entrega diferente do Faturamento o res.partner do
        #  Endereço de Cobrança precisa estar com o campo company_type com
        #  Person/Pessoa e não Company/Empresa.
        #  TODO: A localização BR deveria sobreescrever o metodo address_get
        #   para ignorar o company_type?
        self.assertEqual(invoice_pick_1.partner_shipping_id, picking_1.partner_id)
        self.assertIn(invoice_pick_1, picking_1.invoice_ids)
        self.assertIn(picking_1, invoice_pick_1.picking_ids)

        invoice_pick_2 = invoicies.filtered(
            lambda t: t.partner_shipping_id == picking_2.partner_id
        )
        self.assertIn(invoice_pick_2, picking_2.invoice_ids)
        self.assertIn(picking_2, invoice_pick_2.picking_ids)

        # Not grouping products with different Operation Fiscal Line
        self.assertEqual(len(invoice_pick_1.invoice_line_ids), 3)
        # TODO: No travis falha o browse aqui
        #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
        #  isso não acontece no caso da empresa de Lucro Presumido
        #  ou quando é feito o teste apenas instalando os modulos
        #  l10n_br_account e em seguida o l10n_br_stock_account
        # for inv_line in invoice_pick_1.invoice_line_ids:
        #    self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")

        invoice_pick_1.unlink()
        invoice_pick_2.unlink()
        pickings = picking_1 | picking_2
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        # Check that invoices for our pickings were deleted
        remaining_invoices = self.env["account.move"].search(
            [("id", "in", [invoice_pick_1.id, invoice_pick_2.id])]
        )
        self.assertFalse(remaining_invoices, "Invoices should be deleted")

        # Caso onde por ter no partner do Endereço de Faturamento o campo
        # company_type com Person o address_get retorna esse partner e
        # permite esse caso do Endereço de Entrega diferente de Faturamento
        # TODO: avaliar se a localização deveria sobreescrever o metodo
        #  address_get para ignorar o campo company_type?

        # Caso onde o Partner tem o Endereço de Entrega definido com o
        # company_type person, um Picking é criado com o Endereço de Entrega e
        # outro com o Endereço Pincipal, hoje são criadas 2 Faturas as duas estão
        # com o partner o Endereço Principal e o partner_shipping_id o
        # Endereço de Entrega
        # TODO: Nesse caso os Pickings deveriam ser agrupados e criado apenas uma
        #  Fatura?
        #  O Picking definido com um partner diferente do Endereço de entrega
        #  ( contato com o campo Type definido como delivery) deve criar a
        #  Fatura com o mesmo partner do Picking?
        #  Isso acontece porque o metodo _get_picking_key considera o partner
        #  do picking https://github.com/OCA/account-invoicing/blob/14.0/
        #  stock_picking_invoicing/wizards/stock_invoice_onshipping.py#L316
        #  é preciso avaliar se deve ser alterado na localização ou mesmo
        #  no modulo stock_picking_invoicing
        picking_3 = self.picking_out_br_5
        self.picking_move_state(picking_3)
        picking_4 = self.picking_out_br_6
        self.picking_move_state(picking_4)
        invoices = create_with_form_inv_onshipping(self.env, picking_3 | picking_4)
        self.assertEqual(len(invoices), 2)
        self.assertEqual(picking_3.invoice_state, "invoiced")
        self.assertEqual(picking_4.invoice_state, "invoiced")

        # Caso Endereço de Fatura diferente do de Entrega
        self.assertIn(picking_3.invoice_ids, invoices)
        self.assertIn(picking_4.invoice_ids, invoices)

    def test_04_picking_split(self):
        """Test Picking Split created with Fiscal Values."""
        picking = self.picking_out_br_2
        picking.action_confirm()
        picking.action_assign()

        for move in picking.move_ids_without_package:
            # Force Split
            move.quantity = 1

        # Return Wizard
        backorder = create_with_form_pck_backorder(self.env, picking)
        self.assertEqual(backorder.invoice_state, "2binvoiced")
        self.assertTrue(backorder.fiscal_operation_id)

        for line in backorder.move_ids:
            self.assertTrue(line.fiscal_operation_id)
            self.assertTrue(line.fiscal_operation_line_id)
            self.assertEqual(line.invoice_state, "2binvoiced")
            self.assertTrue(line.fiscal_tax_ids, "Taxes in Split Picking are missing.")

        self.picking_move_state(backorder)

    # Testando o Lucro Presumido
    def test_05_invoicing_picking_lucro_presumido(self):
        """Test Invoicing Picking - Lucro Presumido"""
        self._change_user_company(self.company_lp)
        picking = self.picking_out_br_lp_1
        nb_invoice_before = self.env["account.move"].search_count([])

        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done", "Change state fail.")
        # Verificar os Valores de Preço pois isso é usado na Valorização do
        # Estoque, o metodo do core é chamado pelo botão Validate

        for line in picking.move_ids:
            # O Campo fiscal_price precisa ser um espelho do price_unit,
            # apesar do onchange p/ preenche-lo sem incluir o compute no campo
            # ele traz o valor do lst_price e falha no teste abaixo
            # TODO - o fiscal_price aqui tbm deve ter um valor negativo ?
            self.assertEqual(line.fiscal_price, line.price_unit)
            # Testa o _get_price_unit_invoice para o caso onde o Preço Padrão
            # do Produto e o Preço Unitário informado é Zero
            line.product_id.standard_price = 0.0
            line.price_unit = 0.0

        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.check_br_invoice_created(invoice, picking)
        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))

        self.run_picking_devolution(picking)

        # Now test behaviour if the invoice is delete
        invoice.unlink()
        self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.env["account.move"].search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_06_fields_freight_insurance_other_costs(self):
        """Test fields Freight, Insurance and Other Costs when
        defined or By Line or By Total in Stock Picking.
        """
        picking = self.picking_out_br_1
        # Por padrão a definição dos campos está por Linha
        picking.company_id.delivery_costs = "line"
        # Teste definindo os valores Por Linha
        for line in picking.move_ids_without_package:
            line.price_unit = 100.0
            line.freight_value = 10.0
            line.insurance_value = 10.0
            line.other_value = 10.0
            line.quantity = line.product_uom_qty

        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done", "Change state fail.")

        # TODO: Os campos Totais não estão sendo atualizados mesmo
        #  rodando os onchanges e confirmando o Picking, na tela esse
        #  problema não acontece
        picking._amount_all()

        self.assertEqual(
            picking.amount_freight_value,
            30.0,
            "Unexpected value for the field Amount Freight in Stock Picking.",
        )
        self.assertEqual(
            picking.amount_insurance_value,
            30.0,
            "Unexpected value for the field Amount Insurance in Stock Picking.",
        )
        self.assertEqual(
            picking.amount_other_value,
            30.0,
            "Unexpected value for the field Amount Other in Stock Picking.",
        )

        # Teste definindo os valores Por Total
        # Por padrão a definição dos campos está por Linha
        picking.company_id.delivery_costs = "total"

        # Caso que os Campos na Linha tem valor
        picking.amount_freight_value = 9.0
        picking.amount_insurance_value = 9.0
        picking.amount_other_value = 9.0

        for line in picking.move_ids:
            self.assertEqual(
                line.freight_value,
                3.0,
                "Unexpected value for the field Freight in Move line.",
            )
            self.assertEqual(
                line.insurance_value,
                3.0,
                "Unexpected value for the field Insurance in Move line.",
            )
            self.assertEqual(
                line.other_value,
                3.0,
                "Unexpected value for the field Other Values in Move line.",
            )

        # Caso que os Campos na Linha não tem valor
        for line in picking.move_ids:
            line.price_unit = 100.0
            line.freight_value = 0.0
            line.insurance_value = 0.0
            line.other_value = 0.0

        picking.company_id.delivery_costs = "total"

        picking.amount_freight_value = 30.0
        picking.amount_insurance_value = 30.0
        picking.amount_other_value = 30.0

        for line in picking.move_ids:
            self.assertEqual(
                line.freight_value,
                10.0,
                "Unexpected value for the field Amount Freight in Stock Picking.",
            )
            self.assertEqual(
                line.insurance_value,
                10.0,
                "Unexpected value for the field Insurance in Move line.",
            )
            self.assertEqual(
                line.other_value,
                10.0,
                "Unexpected value for the field Other Values in Move line.",
            )

        invoice = create_with_form_inv_onshipping(self.env, picking)
        # Confirm Invoice
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        self.assertTrue(
            invoice.fiscal_document_id,
            "Freight, Insurance and Other Costs case should has Fiscal Document.",
        )

    def test_07_compatible_with_international_case(self):
        """
        Test of compatible with international case, create Invoice but not for Brazil.
        """
        picking = self.picking_out_1
        picking.set_to_be_invoiced()
        picking.fiscal_operation_id = False
        # Force product availability
        for move in picking.move_ids_without_package:
            # test split
            move.product_uom_qty = 2
            move.quantity = 1
        # Return Wizard
        backorder = create_with_form_pck_backorder(self.env, picking)
        self.assertEqual(backorder.invoice_state, "2binvoiced")
        self.assertFalse(backorder.fiscal_operation_id)

        for line in backorder.move_ids:
            self.assertFalse(line.fiscal_operation_id)
            self.assertFalse(line.fiscal_operation_line_id)
            self.assertEqual(line.invoice_state, "2binvoiced")

        self.picking_move_state(backorder)

        self.assertEqual(picking.state, "done")
        # Switch to picking company for invoice creation
        self._change_user_company(picking.company_id)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        # Confirm Invoice
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        # Check Invoice Type
        self.assertEqual(
            invoice.move_type, "out_invoice", "Invoice Type should be Out Invoice"
        )
        # Caso Internacional não deve ter Documento Fiscal associado
        self.assertFalse(
            invoice.fiscal_document_id,
            "International case should not has Fiscal Document.",
        )

    def test_08_picking_extra_vals(self):
        """Test Picking Extra Vals created with Fiscal Values."""
        picking = self.picking_out_br_2

        for line in picking.move_ids:
            # Force Split
            line.quantity = 10

        picking.button_validate()

    def test_09_form_stock_picking(self):
        """Test Stock Picking with Form"""
        picking_form = Form(self.picking_out_br_2)
        picking_form.save()
        stock_move_form = Form(self.picking_out_br_2.move_ids[0])
        stock_move_form.product_uom_qty = 10
        # Testa o _onchange_product_quantity
        stock_move_form.price_unit = 0.0
        stock_move_form.save()

    def test_10_simples_nacional(self):
        """Test case of Simples Nacional"""
        self._change_user_company(self.company_sn)
        picking = self.picking_out_br_sn_1
        for line in picking.move_ids:
            # Testa _get_price_unit
            line.price_unit = 0.0
        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done", "Change state fail.")
        invoice = create_with_form_inv_onshipping(self.env, picking)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        self.assertTrue(
            invoice.fiscal_document_id,
            "Simples Nacional case should has Fiscal Document.",
        )

    def test_11_generate_document_number_on_packing(self):
        """Test Invoicing Picking"""
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "pack"
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids_without_package:
            move.quantity = move.product_uom_qty
        picking.action_put_in_pack()
        picking.button_validate()
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.check_br_invoice_created(invoice, picking)

        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

    def test_12_generate_document_number_on_validating(self):
        """Test Invoicing Picking"""
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "validate"

        self.picking_move_state(picking)
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.check_br_invoice_created(invoice, picking)
        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

    def test_13_generate_document_number_on_invoice_create_wizard(self):
        """Test Invoicing Picking"""
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "validate"

        self.picking_move_state(picking)
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = create_with_form_inv_onshipping(self.env, picking)
        self.check_br_invoice_created(invoice, picking)

        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )
