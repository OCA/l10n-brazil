# Copyright (C) 2019-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from .common import TestBrPickingInvoicingCommon


class InvoicingPickingTest(TestBrPickingInvoicingCommon):
    """Test invoicing picking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_invoicing_picking(self):
        """Test Invoicing Picking"""
        self._change_user_company(self.env.ref("base.main_company"))
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        self.picking_move_state(picking)
        # Verificar os Valores de Preço pois isso é usado na Valorização do
        # Estoque, o metodo do core é chamado pelo botão Validate

        for line in picking.move_ids:
            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda por padrão deve trazer o valor o Preço de Custo
            # e não o de Venda, ex.: Simples Remessa, Remessa p/
            # Industrialiazação e etc, mas o valor informado pelo usuário deve
            # ter prioridade.
            # Os metodos do stock/core alteram o valor p/
            # negativo por isso o abs

            self.assertEqual(
                abs(line.price_unit),
                line.product_id.with_company(line.company_id).standard_price,
            )
            # O Campo fiscal_price precisa ser um espelho do price_unit,
            # apesar do onchange p/ preenche-lo sem incluir o compute no campo
            # ele traz o valor do lst_price e falha no teste abaixo
            # TODO - o fiscal_price aqui tbm deve ter um valor negativo ?

        invoice = self.create_invoice_wizard(picking)
        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                picking.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            # TODO: No travis falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(line.tax_ids, "Taxes in invoice lines are missing.")

            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda precisam informar o Preço de Custo e não o de
            # Venda, ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
            # Aqui o campo não pode ser negativo
            self.assertEqual(
                line.price_unit,
                line.product_id.with_company(line.company_id).standard_price,
            )
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        self.assertTrue(
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        picking_devolution = self.return_picking_wizard(picking)
        self.assertEqual(picking_devolution.invoice_state, "2binvoiced")
        self.assertTrue(
            picking_devolution.fiscal_operation_id, "Missing Fiscal Operation."
        )
        for line in picking_devolution.move_ids:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )
        self.picking_move_state(picking_devolution)
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")

    def test_picking_invoicing_by_product2(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking.
        We use same partner for 2 picking so we should have 1 invoice with 3
        lines (and qty 2)
        :return:
        """
        nb_invoice_before = self.env["account.move"].search_count([])
        self._change_user_company(self.env.ref("base.main_company"))
        self.env["account.move"].search_count([])
        self.env.ref("l10n_br_base.res_partner_cliente1_sp").write({"type": "invoice"})
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        self.picking_move_state(picking)
        picking2 = self.env.ref("l10n_br_stock_account.main_company-picking_2")
        self.picking_move_state(picking2)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking2.state, "done")
        pickings = picking | picking2
        invoice = self.create_invoice_wizard(pickings)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(invoice, picking2.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(picking2, invoice.picking_ids)
        for inv_line in invoice.invoice_line_ids:
            # qty = 4 because 2 for each stock.move
            self.assertEqual(inv_line.quantity, 4)
            # Price Unit e Fiscal Price devem ser positivos
            price_unit_mv_line = picking.move_ids.filtered(
                lambda mv, inv_line=inv_line: mv.product_id == inv_line.product_id
            ).mapped("price_unit")[0]
            self.assertEqual(
                inv_line.price_unit,
                price_unit_mv_line,
            )
            self.assertEqual(
                inv_line.fiscal_price,
                price_unit_mv_line,
            )

            # TODO: No travis falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(inv_line.tax_ids,
            # "Error to map Sale Tax in invoice.line.")

        # Now test behaviour if the invoice is delete
        invoice.unlink()
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.env["account.move"].search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_picking_invoicing_by_product3(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking, but 1 picking are the one
        address of the other partner so we should have 2 invoicies
        with 3 lines (and qty 2)
        :return:
        """
        nb_invoice_before = self.env["account.move"].search_count([])
        self._change_user_company(self.env.ref("base.main_company"))
        self.env["account.move"].search_count([])
        self.env.ref("l10n_br_base.res_partner_cliente1_sp").write({"type": "invoice"})
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_3")
        self.picking_move_state(picking)
        picking2 = self.env.ref("l10n_br_stock_account.main_company-picking_4")
        self.picking_move_state(picking2)
        self.assertEqual(picking.state, "done")
        self.assertEqual(picking2.state, "done")
        pickings = picking | picking2
        invoicies = self.create_invoice_wizard(pickings)
        self.assertEqual(len(invoicies), 2)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")
        invoice_pick_1 = invoicies.filtered(
            lambda t: t.partner_id == picking.partner_id
        )
        # TODO - está trazendo o mesmo Partner apesar de ser um endereço do
        #  de outro principal, o metodo address_get chamado pelo
        #  get_invoice_partner está trazendo o primeiro is_company. Isso
        #  significa que no caso de uso de ter um Picking para ser Faturado
        #  sem relação com um Pedido de Venda/Compras a opção de ter um
        #  Endereço de Entrega diferente do de Faturamento precirá ser
        #  feita manualmente na Fatura/Doc Fiscal criados.
        self.assertEqual(invoice_pick_1.partner_id, picking.partner_id)
        self.assertIn(invoice_pick_1, picking.invoice_ids)
        self.assertIn(picking, invoice_pick_1.picking_ids)

        invoice_pick_2 = invoicies.filtered(
            lambda t: t.partner_id == picking2.partner_id
        )
        self.assertIn(invoice_pick_2, picking2.invoice_ids)

        self.assertIn(picking2, invoice_pick_2.picking_ids)

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
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.env["account.move"].search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_picking_split(self):
        """Test Picking Split created with Fiscal Values."""
        self._change_user_company(self.env.ref("base.main_company"))
        picking2 = self.env.ref("l10n_br_stock_account.main_company-picking_2")

        self._run_fiscal_onchanges(picking2)

        for line in picking2.move_ids:
            self._run_fiscal_line_onchanges(line)

        picking2.action_confirm()
        picking2.action_assign()

        for move in picking2.move_ids_without_package:
            # Force Split
            move.quantity_done = 1

        # Return Wizard
        backorder = self.create_backorder_wizard(picking2)
        self.assertEqual(backorder.invoice_state, "2binvoiced")
        self.assertTrue(backorder.fiscal_operation_id)

        for line in backorder.move_ids:
            self.assertTrue(line.fiscal_operation_id)
            self.assertTrue(line.fiscal_operation_line_id)
            self.assertEqual(line.invoice_state, "2binvoiced")
            self.assertTrue(line.fiscal_tax_ids, "Taxes in Split Picking are missing.")

        self.picking_move_state(backorder)

    # Testando o Lucro Presumido
    def test_invoicing_picking_lucro_presumido(self):
        """Test Invoicing Picking - Lucro Presumido"""

        self._change_user_company(self.env.ref("l10n_br_base.empresa_lucro_presumido"))
        picking = self.env.ref("l10n_br_stock_account.lucro_presumido-picking_1")
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

        invoice = self.create_invoice_wizard(picking)
        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        # Campo 'Consumidor Final' deve ser igual ao do picking
        self.assertEqual(invoice.ind_final, picking.ind_final)
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                picking.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda precisam informar o Preço de Custo e não o de
            # Venda, ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
            # Aqui o campo não pode ser negativo
            # self.assertEqual(line.price_unit, line.product_id.standard_price)
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )
            self.assertTrue(
                line.fiscal_tax_ids, "Error to map fiscal_tax_ids in invoice line."
            )
            assert line.ind_final, "Error field ind_final in Invoice Line not None"
            # Verifica se o campo tax_ids da Fatura esta igual ao da Separação
            mv_line = picking.move_ids.filtered(
                lambda ln, line=line: ln.product_id == line.product_id
                and ln.fiscal_operation_id == line.fiscal_operation_id
            )
            self.assertEqual(
                line.tax_ids,
                mv_line.tax_ids,
                "Taxes in invoice lines are different from move lines.",
            )

        self.assertTrue(
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        picking_devolution = self.return_picking_wizard(picking)
        self.assertEqual(picking_devolution.invoice_state, "2binvoiced")
        self.assertTrue(
            picking_devolution.fiscal_operation_id, "Missing Fiscal Operation."
        )
        for line in picking_devolution.move_ids:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )
        self.picking_move_state(picking_devolution)
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")

        # Now test behaviour if the invoice is delete
        invoice.unlink()

        self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.env["account.move"].search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_fields_freight_insurance_other_costs(self):
        """Test fields Freight, Insurance and Other Costs when
        defined or By Line or By Total in Stock Picking.
        """

        self._change_user_company(self.env.ref("base.main_company"))
        # Por padrão a definição dos campos está por Linha
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        picking.company_id.delivery_costs = "line"
        # Teste definindo os valores Por Linha
        for line in picking.move_ids_without_package:
            line.price_unit = 100.0
            line.freight_value = 10.0
            line.insurance_value = 10.0
            line.other_value = 10.0
            line.quantity_done = line.product_uom_qty

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

        invoice = self.create_invoice_wizard(picking)
        # Confirm Invoice
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        self.assertTrue(
            invoice.fiscal_document_id,
            "Freight, Insurance and Other Costs case should has Fiscal Document.",
        )

    def test_compatible_with_international_case(self):
        """
        Test of compatible with international case, create Invoice but not for Brazil.
        """
        picking = self.env.ref("stock_picking_invoicing.stock_picking_invoicing_2")
        self._run_fiscal_onchanges(picking)
        # Force product availability
        for move in picking.move_ids_without_package:
            self._run_fiscal_line_onchanges(move)
            # test split
            move.product_uom_qty = 2
            move.quantity_done = 1

        # Return Wizard
        backorder = self.create_backorder_wizard(picking)
        self.assertEqual(backorder.invoice_state, "2binvoiced")
        self.assertFalse(backorder.fiscal_operation_id)

        for line in backorder.move_ids:
            self.assertFalse(line.fiscal_operation_id)
            self.assertFalse(line.fiscal_operation_line_id)
            self.assertEqual(line.invoice_state, "2binvoiced")

        self.picking_move_state(backorder)

        self.assertEqual(picking.state, "done")
        invoice = self.create_invoice_wizard(picking)
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

    def test_picking_extra_vals(self):
        """Test Picking Extra Vals created with Fiscal Values."""
        self._change_user_company(self.env.ref("base.main_company"))
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_2")

        self._run_fiscal_onchanges(picking)

        for line in picking.move_ids:
            self._run_fiscal_line_onchanges(line)
            # Force Split
            line.quantity_done = 10

        picking.button_validate()

    def test_form_stock_picking(self):
        """Test Stock Picking with Form"""

        picking_form = Form(
            self.env.ref("l10n_br_stock_account.main_company-picking_2")
        )
        picking_form.save()
        stock_move_form = Form(
            self.env.ref("l10n_br_stock_account.main_company-move_2_1")
        )
        stock_move_form.product_uom_qty = 10
        # Testa o _onchange_product_quantity
        stock_move_form.price_unit = 0.0
        stock_move_form.save()

    def test_simples_nacional(self):
        """Test case of Simples Nacional"""
        self._change_user_company(self.env.ref("l10n_br_base.empresa_simples_nacional"))
        picking = self.env.ref("l10n_br_stock_account.simples_nacional-picking_1")
        for line in picking.move_ids:
            # Testa _get_price_unit
            line.price_unit = 0.0
        self.picking_move_state(picking)
        self.assertEqual(picking.state, "done", "Change state fail.")
        # Testes falhando apenas no CI, a Operação Fiscal por algum motivo
        # tem o campo journal_id preenchida com o Diário Miscelanios o que
        # causa o erro abaixo
        # File "/opt/odoo/addons/account/models/account_move.py", line 1931,
        #  in _check_journal_type
        # raise ValidationError(_("The chosen journal has a type that is
        # not compatible with your invoice type. Sales operations should go
        # to 'sale' journals, and purchase operations to 'purchase' ones."))
        # odoo.exceptions.ValidationError: The chosen journal has a type that
        # is not compatible with your invoice type. Sales operations should go
        #  to 'sale' journals, and purchase operations to 'purchase' ones.
        # TODO: teria alguma forma de corrigir? Por enquanto está sendo
        # preciso preenche o campo com o Diário correto para evitar o erro
        journal = self.env.ref(
            "l10n_br_stock_account.simples_remessa_journal_simples_nacional"
        )
        of_simples_remessa = self.env.ref("l10n_br_fiscal.fo_simples_remessa")
        of_simples_remessa.journal_id = journal

        invoice = self.create_invoice_wizard(picking)
        # Confirm Invoice
        invoice.action_post()
        self.assertEqual(invoice.state, "posted", "Invoice should be in state Posted")
        self.assertTrue(
            invoice.fiscal_document_id,
            "Simples Nacional case should has Fiscal Document.",
        )

    def test_generate_document_number_on_packing(self):
        """Test Invoicing Picking"""
        self._change_user_company(self.env.ref("base.main_company"))
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        # self._run_fiscal_onchanges(picking)
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "pack"

        self._run_fiscal_onchanges(picking)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids_without_package:
            self._run_fiscal_line_onchanges(move)
            move.quantity_done = move.product_uom_qty

        picking.action_put_in_pack()
        picking.button_validate()
        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = self.create_invoice_wizard(picking)
        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)

        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                picking.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            self.assertEqual(
                line.price_unit,
                line.product_id.with_company(line.company_id).standard_price,
            )
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        self.assertTrue(
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

    def test_generate_document_number_on_validating(self):
        """Test Invoicing Picking"""
        self._change_user_company(self.env.ref("base.main_company"))
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        # self._run_fiscal_onchanges(picking)
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "validate"

        self.picking_move_state(picking)

        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = self.create_invoice_wizard(picking)
        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)

        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                picking.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            self.assertEqual(
                line.price_unit,
                line.product_id.with_company(line.company_id).standard_price,
            )
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        self.assertTrue(
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )

    def test_generate_document_number_on_invoice_create_wizard(self):
        """Test Invoicing Picking"""
        self._change_user_company(self.env.ref("base.main_company"))
        picking = self.env.ref("l10n_br_stock_account.main_company-picking_1")
        # Testa os Impostos Dedutiveis
        picking.fiscal_operation_id.deductible_taxes = True
        nb_invoice_before = self.env["account.move"].search_count([])
        picking.picking_type_id.pre_generate_fiscal_document_number = "validate"

        self.picking_move_state(picking)

        picking.set_to_be_invoiced()
        self.assertTrue(picking.document_number)

        invoice = self.create_invoice_wizard(picking)
        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(
            invoice.partner_id, self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        )
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)

        nb_invoice_after = self.env["account.move"].search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                picking.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            self.assertEqual(
                line.price_unit,
                line.product_id.with_company(line.company_id).standard_price,
            )
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )

        self.assertTrue(
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        self.assertEqual(picking.document_number, invoice.document_number)
        self.assertEqual(
            picking.document_number, invoice.fiscal_document_id.document_number
        )
