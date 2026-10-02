# Copyright (C) 2019-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_pck_backorder,
    create_with_form_return_picking,
)

from .common import TestBrPickingInvoicingCommon
from .tools import create_br_journal_and_set_fiscal_ops


class InvoicingPickingTest(TestBrPickingInvoicingCommon):
    """Test invoicing picking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Pickings usados apenas pelos testes desta classe (o common BR cria
        # só empresas/parceiros/Operações Fiscais): assim as classes que herdam
        # aquele common sem usar esses Pickings não pagam a criação deles.
        # (o create_picking_br_company é classmethod, ver o comentário no common)
        # Picking Out Empresa principal do testes company_1_data
        cls.picking_out_br_1 = cls.create_picking_br_company(cls.env.company)
        cls.picking_out_br_2 = cls.create_picking_br_company(cls.env.company)
        cls.picking_out_br_3 = cls.create_picking_br_company(
            cls.env.company, delivery_address=True
        )
        cls.picking_out_br_4 = cls.create_picking_br_company(cls.env.company)
        cls.picking_out_br_5 = cls.create_picking_br_company(
            cls.env.company, delivery_address=True
        )
        cls.picking_out_br_6 = cls.create_picking_br_company(cls.env.company)

    def test_01_invoicing_picking(self):
        """Test Invoicing Picking"""
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        self.picking_move_state(picking)
        self.invoice_pickings(picking)
        picking_devolution = self.run_picking_devolution(picking)
        self.invoice_pickings(picking_devolution)

    def test_02_picking_invoicing_by_product2(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking.
        We use same partner for 2 picking so we should have 1 invoice with 3
        lines (and qty 2)
        :return:
        """
        nb_invoice_before = self.env["account.move"].search_count([])
        picking_1 = self.picking_out_br_1
        self.picking_move_state(picking_1)
        picking_2 = self.picking_out_br_2
        self.picking_move_state(picking_2)
        invoice = self.invoice_pickings(picking_1 | picking_2)
        self.assertEqual(len(invoice), 1)
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
        picking_1 = self.picking_out_br_3
        self.picking_move_state(picking_1)
        picking_2 = self.picking_out_br_4
        self.picking_move_state(picking_2)
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

    def test_05_invoicing_picking_lucro_presumido(self):
        """Test Invoicing Picking - Lucro Presumido"""
        company_lp = self.create_empresa_lucro_presumido()
        self._change_user_company(company_lp)
        picking = self.create_picking_br_company(company_lp)
        self.picking_move_state(picking)
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

        self.invoice_pickings(picking)
        self.run_picking_devolution(picking)

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

    def test_08_picking_extra_vals_with_form(self):
        """Picking de Saída validado com os valores fiscais informados.
        O Picking de teste é validado pelas duas vias: pelo Form (caminho da UI,
        que NÃO pode perder os valores fiscais informados na linha) e pela ORM,
        com a quantidade informada pelo usuário.
        """
        # 1) Via Form: o Form não pode perder os valores fiscais da linha
        picking_form = Form(self.picking_out_br_2)
        picking_form.save()
        stock_move_form = Form(self.picking_out_br_2.move_ids[0])
        stock_move_form.product_uom_qty = 10
        # Testa o _onchange_product_quantity
        stock_move_form.price_unit = 0.0
        stock_move_form.save()
        # O Form não pode perder os valores fiscais da linha
        stock_move = self.picking_out_br_2.move_ids[0]
        self.assertEqual(stock_move.product_uom_qty, 10)
        self.assertTrue(stock_move.fiscal_operation_id, "Missing Fiscal Operation.")

        # 2) Via ORM: o Picking é validado com os valores fiscais informados
        picking = self.picking_out_br_2
        for line in picking.move_ids:
            # Force Split
            line.quantity = 10

        picking.button_validate()
        # O Picking é validado com os valores fiscais informados no Form
        self.assertEqual(picking.state, "done", "Change state fail.")
        self.assertEqual(picking.invoice_state, "2binvoiced")
        self.assertTrue(
            picking.fiscal_operation_id, "Missing Fiscal Operation in Picking."
        )
        for line in picking.move_ids:
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_tax_ids, "Taxes in Validated Picking are missing."
            )

    def test_09_simples_nacional(self):
        """Test case of Simples Nacional"""
        company_sn = self.create_empresa_simples_nacional()
        self._change_user_company(company_sn)
        picking = self.create_picking_br_company(company_sn)
        for line in picking.move_ids:
            # Testa _get_price_unit
            line.price_unit = 0.0
        self.picking_move_state(picking)
        invoice = create_with_form_inv_onshipping(self.env, picking)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        self.assertTrue(
            invoice.fiscal_document_id,
            "Simples Nacional case should has Fiscal Document.",
        )

    def test_10_generate_document_number(self):
        """O Número do Documento Fiscal pode ser gerado em 3 momentos.
        O campo `pre_generate_fiscal_document_number` do Picking Type decide
        quando o Número é gerado: "pack" (ao pôr o Picking em pacote),
        "validate" (na validação do Picking) ou "invoice_wizard" (só pelo
        Wizard de faturamento). Nos três casos o Número do Picking é o mesmo do
        Documento Fiscal da Fatura criada.
        """
        # 1) "pack": Número gerado ao pôr o Picking em pacote
        picking = self.picking_out_br_1
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        picking.picking_type_id.pre_generate_fiscal_document_number = "pack"
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids_without_package:
            move.quantity = move.product_uom_qty
        picking.action_put_in_pack()
        picking.button_validate()
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = self.invoice_pickings(picking)

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

        # 2) "validate": Número gerado pelo button_validate do Picking
        picking = self.create_picking_br_company(self.env.company)
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        picking.picking_type_id.pre_generate_fiscal_document_number = "validate"

        self.picking_move_state(picking)
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = self.invoice_pickings(picking)

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

        # Chamar o gerador novamente não deve gerar um novo número
        document_serie = picking.document_serie
        document_number = picking.document_number
        picking._generate_document_number()
        self.assertEqual(picking.document_serie, document_serie)
        self.assertEqual(picking.document_number, document_number)

        # 3) "invoice_wizard": só é tratado no _pre_generate_document_number do
        #    Wizard, diferente do "validate" que é tratado no button_validate do
        #    Picking, então o Número NÃO existe antes do Wizard
        picking = self.create_picking_br_company(self.env.company)
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        picking.picking_type_id.pre_generate_fiscal_document_number = "invoice_wizard"

        self.picking_move_state(picking)
        self.assertFalse(
            picking.document_number,
            "Document Number should be generated only by the Wizard.",
        )
        picking.set_to_be_invoiced()
        invoice = self.invoice_pickings(picking)
        self.assertTrue(
            picking.document_number,
            "Document Number was not generated by the Wizard.",
        )
        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

    def test_11_onchange_invoice_state_and_get_price_unit(self):
        """Onchange da Operação Fiscal padrão e o `_get_price_unit` do Picking.
        O onchange `_onchange_invoice_state` informa a Operação Fiscal padrão
        da Empresa/Picking Type quando o Picking não tem uma e o
        `_get_price_unit` deve respeitar o contrato do core (dict por Stock Lot)
        e usar o Preço de Custo nas Operações Fiscais de Saída.
        """
        picking = self.picking_out_br_1

        # 1) Onchange do Invoice State deve informar a Operação Fiscal padrão
        picking.fiscal_operation_id = False
        picking.picking_type_id.fiscal_operation_id = False
        self.company_test.stock_out_fiscal_operation_id = self.op_simples_remessa

        picking._onchange_invoice_state()
        self.assertEqual(picking.fiscal_operation_id, self.op_simples_remessa)

        # 2) _get_price_unit: o Onchange acima deixa a Operação Fiscal de Saída
        #    informada no Picking
        self.picking_move_state(picking)
        move = picking.move_ids[0]

        # Caso Brasileiro de Saída: o valor é o Preço de Custo
        self.assertEqual(
            move._get_price_unit(),
            {self.env["stock.lot"]: move.product_id.standard_price},
        )

        # Sem Operação Fiscal (caso internacional) o resultado é o do core
        move.fiscal_operation_id = False
        self.assertIsInstance(move._get_price_unit(), dict)

    def test_12_picking_in_br_invoicing_price_cases(self):
        """Preço da Fatura de Entrada (in_invoice) criada do Picking.
        Sem valor informado no Stock Move o preço deve vir do método do super
        (Vendedor/Preço de Custo) e não ficar 0; com valor informado pelo
        usuário, o valor informado tem prioridade.
        """
        # A Operação Fiscal de Entrada precisa de um Diário de Compra para a
        # criação do documento de entrada (in_invoice) -- o mesmo Diário serve
        # os dois casos
        create_br_journal_and_set_fiscal_ops(
            self.env,
            self.company_test,
            self.op_entrada_remessa,
            journal_type="purchase",
        )

        # 1) Preço não informado no Stock Move
        picking = self.create_picking_br_company(self.company_test, code="incoming")
        self.picking_move_state(picking)

        for line in picking.move_ids:
            # Preço não informado no Stock Move e sem impostos de fornecedor
            # para o valor esperado ser exato
            line.product_id.standard_price = 100.0
            line.product_id.supplier_taxes_id = False
            line.price_unit = 0.0

        invoice = self.invoice_pickings(picking)
        self.assertEqual(invoice.move_type, "in_invoice")
        for line in invoice.invoice_line_ids:
            self.assertEqual(
                100.0,
                line.price_unit,
                "Supplier Invoice should get the price from the super method,"
                " not 0.",
            )
            # O fiscal_price precisa ser um espelho do price_unit da linha da
            # Fatura (calculado pelo _compute_fiscal_price do l10n_br_fiscal)
            self.assertEqual(
                line.fiscal_price,
                line.price_unit / (line.product_id.uot_factor or 1.0),
                "fiscal_price must mirror the Invoice Line price_unit.",
            )

        # 2) Valor informado pelo usuário tem prioridade na Entrada
        picking = self.create_picking_br_company(self.company_test, code="incoming")
        self.picking_move_state(picking)

        for line in picking.move_ids:
            # Preço informado tem prioridade sobre o Preço de Custo
            line.product_id.standard_price = 50.0
            line.price_unit = 100.0

        invoice = self.invoice_pickings(picking)
        self.assertEqual(invoice.move_type, "in_invoice")
        for line in invoice.invoice_line_ids:
            self.assertEqual(100.0, line.price_unit)

    def test_13_picking_in_br_invoicing_in_refund(self):
        """`in_refund` com valor informado no Stock Move tem prioridade.
        Os outros casos do método são cobertos ponta a ponta: in_invoice sem
        valor informado (test_12) e in_refund
        sem valor informado (test_14).
        """
        picking = self.create_picking_br_company(self.company_test, code="incoming")
        move = picking.move_ids
        # Garante o caso Brasileiro, que é caracterizado pela Operação Fiscal
        move.fiscal_operation_id = self.op_entrada_remessa
        move.product_id.standard_price = 100.0
        move.price_unit = 150.0
        self.assertEqual(
            150.0,
            move._get_price_unit_invoice("in_refund", picking.partner_id),
        )

    def test_14_picking_in_br_return_invoicing(self):
        """Devolução do Picking de Entrada — out op + in_refund.
        A devolução de uma Entrada recebe a Operação Fiscal de retorno
        (Simples Remessa, tipo out) e é faturada como in_refund (documento de
        compra), por isso as Operações Fiscais envolvidas precisam de um
        Diário de Compra.
        """
        create_br_journal_and_set_fiscal_ops(
            self.env,
            self.company_test,
            self.op_entrada_remessa | self.op_simples_remessa,
            journal_type="purchase",
        )
        picking = self.create_picking_br_company(self.company_test, code="incoming")
        self.picking_move_state(picking)
        for line in picking.move_ids:
            line.product_id.standard_price = 100.0
            line.product_id.supplier_taxes_id = False
            line.price_unit = 0.0

        invoice = self.invoice_pickings(picking)
        self.assertEqual(invoice.move_type, "in_invoice")

        picking_devolution = self.run_picking_devolution(picking)
        self.assertEqual(
            picking_devolution.fiscal_operation_id,
            self.op_simples_remessa,
            "The return Picking must get the return Fiscal Operation.",
        )
        for line in picking_devolution.move_ids:
            line.price_unit = 0.0

        invoice_devolution = create_with_form_inv_onshipping(
            self.env, picking_devolution
        )
        self.assertEqual(invoice_devolution.move_type, "in_refund")
        for line in invoice_devolution.invoice_line_ids:
            self.assertEqual(
                100.0,
                line.price_unit,
                "Supplier Refund should get the price from the super method, not 0.",
            )
            # O fiscal_price precisa ser um espelho do price_unit da linha da
            # Fatura (calculado pelo _compute_fiscal_price do l10n_br_fiscal)
            self.assertEqual(
                line.fiscal_price,
                line.price_unit / (line.product_id.uot_factor or 1.0),
                "fiscal_price must mirror the Invoice Line price_unit.",
            )

    def test_15_invoicing_without_fiscal_operation_journal(self):
        """Operação Fiscal sem Diário e sem Operação Fiscal de retorno.
        É o Diário da Operação Fiscal que define o Diário da Fatura (ver
        `_get_journal` do Wizard) e a Operação Fiscal de retorno que o Wizard de
        devolução usa (ver `_prepare_picking_default_values`): sem eles o Wizard
        deve avisar o usuário.
        """
        picking = self.picking_out_br_1
        self.picking_move_state(picking)
        picking.set_to_be_invoiced()

        # 1) Operação Fiscal sem Diário
        journal = picking.fiscal_operation_id.journal_id
        picking.fiscal_operation_id.journal_id = False

        env = self.env(
            context={
                **self.env.context,
                "default_fiscal_operation_journal": True,
            }
        )
        with self.assertRaises(UserError):
            create_with_form_inv_onshipping(env, picking)
        # O Diário é devolvido à Operação Fiscal: o bloco 2 usa a MESMA
        # Operação Fiscal de Saída
        picking.fiscal_operation_id.journal_id = journal

        # 2) Operação Fiscal sem Operação Fiscal de retorno
        picking.fiscal_operation_id.return_fiscal_operation_id = False

        with self.assertRaises(UserError):
            create_with_form_return_picking(self.env, picking)

    def test_16_invoicing_picking_with_invoice_address(self):
        """Picking cujo parceiro tem Endereço de Faturamento próprio.
        A Fatura NÃO é criada com o parceiro do Picking: o parceiro usado é o
        Endereço de Faturamento (`_get_partner_to_invoice`, ver o comentário em
        `check_br_invoice_created`), o parceiro do Picking vai para o
        `partner_shipping_id` da Fatura e o Documento Fiscal recebe o Endereço
        de Faturamento (`_get_fiscal_partner`).
        """
        invoice_address = self.partner_br_stock_1_delivery_address
        invoice_address.type = "invoice"

        picking = self.create_picking_br_company(self.env.company)
        self.picking_move_state(picking)
        # O parceiro do Picking é o principal, o Endereço de Faturamento é
        # resolvido pelo wizard no momento da criação da Fatura
        self.assertEqual(picking.partner_id, self.partner_br_stock_1)
        self.assertEqual(picking._get_partner_to_invoice(), invoice_address.id)

        # Aqui NÃO pode ser usado o `invoice_pickings`/`check_br_invoice_created`
        # do common: a assertiva de parceiro dele pressupõe parceiro sem
        # Endereço de Faturamento diferente do principal
        invoice = create_with_form_inv_onshipping(self.env, picking)

        self.assertEqual(invoice.partner_id, invoice_address)
        self.assertNotEqual(invoice.partner_id, picking.partner_id)
        # O parceiro do Picking é o Endereço de Entrega da Fatura
        self.assertEqual(invoice.partner_shipping_id, picking.partner_id)
        # O Documento Fiscal também fica com o Endereço de Faturamento
        self.assertEqual(invoice.fiscal_document_id.partner_id, invoice_address)
