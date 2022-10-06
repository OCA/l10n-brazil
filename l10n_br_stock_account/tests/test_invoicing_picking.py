# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, SavepointCase


class InvoicingPickingTest(SavepointCase):
    """Test invoicing picking"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_picking = cls.env["stock.picking"]
        cls.invoice_model = cls.env["account.move"]
        cls.invoice_wizard = cls.env["stock.invoice.onshipping"]
        cls.stock_return_picking = cls.env["stock.return.picking"]
        cls.stock_picking_sp = cls.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-1"
        )
        cls.stock_picking_sp_lp = cls.env.ref(
            "l10n_br_stock_account.demo_l10n_br_stock_account-picking-1"
        )
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.company_lucro_presumido = cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido"
        )
        cls.company = cls.env.ref("base.main_company")

    def _run_fiscal_onchanges(self, record):
        record._onchange_fiscal_operation_id()

    def _run_fiscal_line_onchanges(self, record):
        record._onchange_product_id_fiscal()
        record._onchange_fiscal_operation_id()
        record._onchange_fiscal_operation_line_id()
        record._onchange_fiscal_taxes()

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def test_invoicing_picking(self):
        """Test Invoicing Picking"""
        self._change_user_company(self.company)

        nb_invoice_before = self.invoice_model.search_count([])
        self._run_fiscal_onchanges(self.stock_picking_sp)

        for line in self.stock_picking_sp.move_lines:
            self._run_fiscal_line_onchanges(line)
            line._onchange_product_quantity()

        self.stock_picking_sp.action_confirm()
        self.stock_picking_sp.action_assign()

        # Force product availability
        for move in self.stock_picking_sp.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        self.stock_picking_sp.button_validate()
        self.assertEqual(self.stock_picking_sp.state, "done", "Change state fail.")
        # Verificar os Valores de Preço pois isso é usado na Valorização do
        # Estoque, o metodo do core é chamado pelo botão Validate

        for line in self.stock_picking_sp.move_lines:
            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda precisam informar o Preço de Custo e não o de
            # Venda, ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
            # Teria algum caso que não deve usar ?

            # Os metodos do stock/core alteram o valor p/
            # negativo por isso o abs
            self.assertEqual(abs(line.price_unit), line.product_id.standard_price)
            # O Campo fiscal_price precisa ser um espelho do price_unit,
            # apesar do onchange p/ preenche-lo sem incluir o compute no campo
            # ele traz o valor do lst_price e falha no teste abaixo
            # TODO - o fiscal_price aqui tbm deve ter um valor negativo ?

        wizard_obj = self.invoice_wizard.with_context(
            active_ids=self.stock_picking_sp.ids,
            active_model=self.stock_picking_sp._name,
            active_id=self.stock_picking_sp.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.with_context(default_company_id=self.company.id).action_generate()
        domain = [("picking_ids", "=", self.stock_picking_sp.id)]
        invoice = self.invoice_model.search(domain)

        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(self.stock_picking_sp.invoice_state, "invoiced")
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertIn(invoice, self.stock_picking_sp.invoice_ids)
        self.assertIn(self.stock_picking_sp, invoice.picking_ids)
        nb_invoice_after = self.invoice_model.search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                self.stock_picking_sp.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            # TODO: No travis falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalanado os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(line.tax_ids, "Taxes in invoice lines are missing.")

            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda precisam informar o Preço de Custo e não o de
            # Venda, ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
            # Aqui o campo não pode ser negativo
            self.assertEqual(line.price_unit, line.product_id.standard_price)
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

        picking = self.stock_picking_sp
        return_wizard_form = Form(
            self.stock_return_picking.with_context(
                dict(active_id=picking.id, active_model="stock.picking")
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

    def test_picking_invoicing_by_product2(self):
        """
        Test the invoice generation grouped by partner/product with 2
        picking and 3 moves per picking.
        We use same partner for 2 picking so we should have 1 invoice with 3
        lines (and qty 2)
        :return:
        """
        nb_invoice_before = self.invoice_model.search_count([])
        self._change_user_company(self.company)
        self.invoice_model.search_count([])
        self.partner.write({"type": "invoice"})
        picking = self.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-1"
        )
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        picking2 = self.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-2"
        )
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
        wizard.with_context(default_company_id=self.company.id).action_generate()
        domain = [("picking_ids", "=", picking.id)]
        invoice = self.invoice_model.search(domain)
        self.assertEqual(len(invoice), 1)
        self.assertEqual(picking.invoice_state, "invoiced")
        self.assertEqual(picking2.invoice_state, "invoiced")
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertIn(invoice, picking.invoice_ids)
        self.assertIn(invoice, picking2.invoice_ids)
        self.assertIn(picking, invoice.picking_ids)
        self.assertIn(picking2, invoice.picking_ids)
        for inv_line in invoice.invoice_line_ids:
            # qty = 4 because 2 for each stock.move
            self.assertEqual(inv_line.quantity, 4)
            # Price Unit e Fiscal Price devem ser positivos
            self.assertEqual(inv_line.price_unit, inv_line.product_id.standard_price)
            self.assertEqual(inv_line.fiscal_price, inv_line.product_id.standard_price)

            # TODO: No travis falha o browse aqui
            #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
            #  isso não acontece no caso da empresa de Lucro Presumido
            #  ou quando é feito o teste apenas instalando os modulos
            #  l10n_br_account e em seguida o l10n_br_stock_account
            # self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")

        # Now test behaviour if the invoice is delete
        invoice.unlink()
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.invoice_model.search_count([])
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
        nb_invoice_before = self.invoice_model.search_count([])
        self._change_user_company(self.company)
        self.invoice_model.search_count([])
        self.partner.write({"type": "invoice"})
        picking = self.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-3"
        )
        picking.action_confirm()
        # Check product availability
        picking.action_assign()
        # Force product availability
        for move in picking.move_ids_without_package:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        picking2 = self.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-4"
        )
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
        wizard.with_context(default_company_id=self.company.id).action_generate()
        domain = [("picking_ids", "in", (picking.id, picking2.id))]
        invoicies = self.invoice_model.search(domain)
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
        #  ou quando é feito o teste apenas instalanado os modulos
        #  l10n_br_account e em seguida o l10n_br_stock_account
        # for inv_line in invoice_pick_1.invoice_line_ids:
        #    self.assertTrue(inv_line.tax_ids, "Error to map Sale Tax in invoice.line.")

        invoice_pick_1.unlink()
        invoice_pick_2.unlink()
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.invoice_model.search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_picking_split(self):
        """Test Picking Split created with Fiscal Values."""
        self._change_user_company(self.company)
        picking2 = self.env.ref(
            "l10n_br_stock_account.demo_main_l10n_br_stock_account-picking-2"
        )

        self._run_fiscal_onchanges(picking2)

        for line in picking2.move_lines:
            self._run_fiscal_line_onchanges(line)
            line._onchange_product_quantity()

        picking2.action_confirm()
        picking2.action_assign()

        for move in picking2.move_ids_without_package:
            # Force Split
            move.quantity_done = 1

        res_dict_for_back_order = picking2.button_validate()
        backorder_wizard = Form(
            self.env[res_dict_for_back_order["res_model"]].with_context(
                res_dict_for_back_order["context"]
            )
        ).save()
        backorder_wizard.process()
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking2.id)]
        )
        self.assertEqual(backorder.invoice_state, "2binvoiced")
        self.assertTrue(backorder.fiscal_operation_id)

        for line in backorder.move_lines:
            self.assertTrue(line.fiscal_operation_id)
            self.assertTrue(line.fiscal_operation_line_id)
            self.assertEqual(line.invoice_state, "2binvoiced")
            self.assertTrue(line.fiscal_tax_ids, "Taxes in Split Picking are missing.")

        backorder.action_confirm()
        backorder.action_assign()
        backorder.button_validate()

    # Testando o Lucro Presumido
    def test_invoicing_picking_lucro_presumido(self):
        """Test Invoicing Picking - Lucro Presumido"""

        self._change_user_company(self.company_lucro_presumido)

        nb_invoice_before = self.invoice_model.search_count([])
        self._run_fiscal_onchanges(self.stock_picking_sp_lp)

        for line in self.stock_picking_sp_lp.move_lines:
            self._run_fiscal_line_onchanges(line)
            line._onchange_product_quantity()

        self.stock_picking_sp_lp.action_confirm()
        self.stock_picking_sp_lp.action_assign()

        # Force product availability
        for move in self.stock_picking_sp_lp.move_ids_without_package:
            move.quantity_done = move.product_uom_qty

        self.stock_picking_sp_lp.button_validate()
        self.assertEqual(self.stock_picking_sp_lp.state, "done", "Change state fail.")
        # Verificar os Valores de Preço pois isso é usado na Valorização do
        # Estoque, o metodo do core é chamado pelo botão Validate

        for line in self.stock_picking_sp_lp.move_lines:
            # No Brasil o caso de Ordens de Entrega que não tem ligação com
            # Pedido de Venda precisam informar o Preço de Custo e não o de
            # Venda, ex.: Simples Remessa, Remessa p/ Industrialiazação e etc.
            # Teria algum caso que não deve usar ?

            # Os metodos do stock/core alteram o valor p/
            # negativo por isso o abs
            self.assertEqual(abs(line.price_unit), line.product_id.standard_price)
            # O Campo fiscal_price precisa ser um espelho do price_unit,
            # apesar do onchange p/ preenche-lo sem incluir o compute no campo
            # ele traz o valor do lst_price e falha no teste abaixo
            # TODO - o fiscal_price aqui tbm deve ter um valor negativo ?
            self.assertEqual(line.fiscal_price, line.price_unit)

        wizard_obj = self.invoice_wizard.with_context(
            active_ids=self.stock_picking_sp_lp.ids,
            active_model=self.stock_picking_sp_lp._name,
            active_id=self.stock_picking_sp_lp.id,
        )
        fields_list = wizard_obj.fields_get().keys()
        wizard_values = wizard_obj.default_get(fields_list)
        wizard = wizard_obj.create(wizard_values)
        wizard.onchange_group()
        wizard.with_context(
            default_company_id=self.company_lucro_presumido.id
        ).action_generate()
        domain = [("picking_ids", "=", self.stock_picking_sp_lp.id)]
        invoice = self.invoice_model.search(domain)

        self.assertTrue(invoice, "Invoice is not created.")
        self.assertEqual(self.stock_picking_sp_lp.invoice_state, "invoiced")
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertIn(invoice, self.stock_picking_sp_lp.invoice_ids)
        self.assertIn(self.stock_picking_sp_lp, invoice.picking_ids)
        nb_invoice_after = self.invoice_model.search_count([])
        self.assertEqual(nb_invoice_before, nb_invoice_after - len(invoice))
        assert invoice.invoice_line_ids, "Error to create invoice line."
        for line in invoice.picking_ids:
            self.assertEqual(
                line.id,
                self.stock_picking_sp_lp.id,
                "Relation between invoice and picking are missing.",
            )
        for line in invoice.invoice_line_ids:
            self.assertTrue(line.tax_ids, "Taxes in invoice lines are missing.")
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
            invoice.fiscal_operation_id,
            "Mapping fiscal operation on wizard to create invoice fail.",
        )
        self.assertTrue(
            invoice.fiscal_document_id,
            "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
        )

        picking = self.stock_picking_sp_lp
        return_wizard_form = Form(
            self.stock_return_picking.with_context(
                dict(active_id=picking.id, active_model="stock.picking")
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

        # Now test behaviour if the invoice is delete
        invoice.unlink()

        self.assertEqual(picking.invoice_state, "2binvoiced")
        nb_invoice_after = self.invoice_model.search_count([])
        # Should be equals because we delete the invoice
        self.assertEqual(nb_invoice_before, nb_invoice_after)

    def test_fields_freight_insurance_other_costs(self):
        """Test fields Freight, Insurance and Other Costs when
        defined or By Line or By Total in Stock Picking.
        """

        self._change_user_company(self.company)

        # Por padrão a definição dos campos está por Linha
        self.stock_picking_sp.company_id.delivery_costs = "line"
        # Teste definindo os valores Por Linha
        for line in self.stock_picking_sp.move_ids_without_package:
            line.price_unit = 100.0
            line.freight_value = 10.0
            line.insurance_value = 10.0
            line.other_value = 10.0
            line.quantity_done = line.product_uom_qty

        self.stock_picking_sp.button_validate()
        self.assertEqual(self.stock_picking_sp.state, "done", "Change state fail.")

        for line in self.stock_picking_sp.move_lines:
            self._run_fiscal_line_onchanges(line)
            line._onchange_product_quantity()

        self.stock_picking_sp.action_confirm()

        # TODO: Os campos Totais não estão sendo atualizados mesmo
        #  rodando os onchanges e confirmando o Picking, na tela esse
        #  problema não acontece
        self.stock_picking_sp._amount_all()

        self.assertEqual(
            self.stock_picking_sp.amount_freight_value,
            30.0,
            "Unexpected value for the field Amount Freight in Stock Picking.",
        )
        self.assertEqual(
            self.stock_picking_sp.amount_insurance_value,
            30.0,
            "Unexpected value for the field Amount Insurance in Stock Picking.",
        )
        self.assertEqual(
            self.stock_picking_sp.amount_other_value,
            30.0,
            "Unexpected value for the field Amount Other in Stock Picking.",
        )

        # Teste definindo os valores Por Total
        # Por padrão a definição dos campos está por Linha
        self.stock_picking_sp.company_id.delivery_costs = "total"

        # Caso que os Campos na Linha tem valor
        self.stock_picking_sp.amount_freight_value = 9.0
        self.stock_picking_sp.amount_insurance_value = 9.0
        self.stock_picking_sp.amount_other_value = 9.0

        for line in self.stock_picking_sp.move_lines:

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
        for line in self.stock_picking_sp.move_lines:
            line.price_unit = 100.0
            line.freight_value = 0.0
            line.insurance_value = 0.0
            line.other_value = 0.0

        self.stock_picking_sp.company_id.delivery_costs = "total"

        self.stock_picking_sp.amount_freight_value = 30.0
        self.stock_picking_sp.amount_insurance_value = 30.0
        self.stock_picking_sp.amount_other_value = 30.0

        self.stock_picking_sp.action_confirm()

        for line in self.stock_picking_sp.move_lines:
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
