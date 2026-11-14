# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.stock_picking_invoicing.tests.common import (
    TestStockPickingInvoicingCommon,
)
from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_return_picking,
)

from .tools import (
    create_and_configure_br_company,
    create_br_journal_and_set_fiscal_ops,
    create_with_form_br_stock_picking,
)


class TestBrPickingInvoicingCommon(TestStockPickingInvoicingCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Give the test user access to the main company, needed by the data
        # shared between companies (base.main_company is a base data record,
        # it does not require demo data)
        cls.env.user.company_ids |= cls.env.ref("base.main_company")
        cls.get_default_groups()

        # Operação Fiscais comuns em todas as empresas
        cls.op_simples_remessa = cls.env.ref("l10n_br_fiscal.fo_simples_remessa")
        cls.op_bonificacao = cls.env.ref("l10n_br_fiscal.fo_bonificacao")
        cls.op_entrada_remessa = cls.env.ref("l10n_br_fiscal.fo_entrada_remessa")

        # Configuração da empresa company_1_data, é a empresa padrão que vem no teste
        # automaticamente, necessário para validar o campo fiscal_tax_ids.
        cls.company_test = cls.env.company
        cls.env.company.write(
            {
                "tax_framework": "1",
                "is_industry": "True",
                "ripi": "True",
                "piscofins_id": cls.env.ref(
                    "l10n_br_fiscal.tax_pis_cofins_simples_nacional"
                ).id,
                "tax_ipi_id": cls.env.ref("l10n_br_fiscal.tax_ipi_outros").id,
                "tax_icms_id": cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").id,
                "legal_nature_id": cls.env.ref("l10n_br_fiscal.legal_nature_2062").id,
                "cnae_main_id": cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "tax_classification_id": cls.env.ref(
                    "l10n_br_fiscal.tax_classification_000001"
                ).id,
            }
        )
        cls.fiscal_ops = (
            cls.op_simples_remessa | cls.op_bonificacao | cls.op_entrada_remessa
        )
        create_br_journal_and_set_fiscal_ops(cls.env, cls.env.company, cls.fiscal_ops)

        # Partners usados nos testes, um principal e outro Endereço de Entrega.
        data_res_partner = {
            "name": "Cliente 2 -SP - Simples Nacional",
            "legal_name": "Cliente 2 SN - SP",
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_sp").id,
            "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            "zip": "18125-000",
            "street_name": "Rua A",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "62.185.456/0001-20",
            "l10n_br_ie_code": "887.273.429.152",
            "fiscal_profile_id": cls.env.ref(
                "l10n_br_fiscal.partner_fiscal_profile_snc"
            ).id,
        }
        cls.partner_br_stock_1 = cls.env["res.partner"].create(data_res_partner)

        data_res_partner_delivery_address = {
            "name": "Cliente 2 - SP - Endereço Entrega",
            "legal_name": "Cliente 2 - SP - Endereço Entrega",
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_sp").id,
            "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            "zip": "04583-120",
            "street_name": "Rua B",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "84.634.860/0001-77",
            "l10n_br_ie_code": "811.510.100.755",
            "fiscal_profile_id": cls.env.ref(
                "l10n_br_fiscal.partner_fiscal_profile_snc"
            ).id,
            # Informações dos Contatos
            "company_type": "person",
            "type": "delivery",
            "parent_id": cls.partner_br_stock_1.id,
        }
        cls.partner_br_stock_1_delivery_address = cls.env["res.partner"].create(
            data_res_partner_delivery_address
        )

        # Os Pickings usados pelos testes do módulo (picking_out_br_*) são
        # criados no setUpClass de cada classe que os usa (ver
        # test_invoicing_picking.py): assim as classes que herdam este common
        # sem usá-los (ex.: l10n_br_sale_stock) não pagam a criação deles.
        # Aqui fica só o que é comum: empresas, parceiros e Operações Fiscais.

    # Classmethods: os Pickings do módulo são criados no `setUpClass` das
    # classes que os usam (ver o comentário no setUpClass do
    # test_invoicing_picking.py) e dependem apenas dos dados da classe.
    @classmethod
    def create_picking_br_company(
        cls, company, code="outgoing", delivery_address=False
    ):
        """Cria um Picking da empresa pelo Form.

        :param code: `code` do Picking Type, que define o Picking: "outgoing"
            (Saída, default, Operações Fiscais de Saída e três linhas) ou
            "incoming" (Entrada, Operação Fiscal de Entrada
            -- `op_entrada_remessa` -- e uma linha, usado pelos testes de
            Fatura de Fornecedor).
        :param delivery_address: usa o Endereço de Entrega como Parceiro (só
            faz sentido no Picking de Saída).
        """
        is_out = code == "outgoing"
        picking_vals = {
            "partner_id": cls.partner_br_stock_1,
            "picking_type_id": cls.env["stock.picking.type"].search(
                [("company_id", "=", company.id), ("code", "=", code)], limit=1
            ),
            "fiscal_operation_id": (
                cls.op_simples_remessa if is_out else cls.op_entrada_remessa
            ),
            "company_id": company,
        }
        if delivery_address:
            picking_vals |= {"partner_id": cls.partner_br_stock_1_delivery_address}

        # A primeira linha é a mesma nos dois Pickings. As Operações Fiscais das
        # linhas são escritas DEPOIS do save: o Form do
        # `create_with_form_br_stock_picking` só aplica `product_id` e
        # `product_uom_qty` em cada linha.
        move_vals = [{"product_id": cls.product_storable_1, "product_uom_qty": 2}]
        if is_out:
            move_vals += [
                {"product_id": cls.product_storable_2, "product_uom_qty": 2},
                {"product_id": cls.product_storable_1, "product_uom_qty": 2},
            ]

        picking_br = create_with_form_br_stock_picking(cls.env, picking_vals, move_vals)
        if is_out:
            picking_br.move_ids[2].fiscal_operation_id = cls.op_bonificacao
        return picking_br

    def create_empresa_lucro_presumido(self):
        """Cria e configura a Empresa de Lucro Presumido usada pelos testes.

        Chamado apenas pelos testes que precisam da Empresa (não no
        `setUpClass`): assim as classes que herdam este common sem usá-la não
        pagam a criação da Empresa, do Plano de Contas e dos Diários.
        """

        # Empresa Lucro Presumido
        legal_nature_2062 = self.env["l10n_br_fiscal.legal.nature"].search(
            [("code", "=", "206-2")]
        )
        fiscal_cnae_3101200 = self.env["l10n_br_fiscal.cnae"].search(
            [("code", "=", "3101-2/00")]
        )
        data_company_lp = {
            "name": "Empresa Lucro Presumido 1",
            "legal_name": "Empresa Lucro Presumido 1",
            "country_id": self.env.ref("base.br").id,
            "state_id": self.env.ref("base.state_br_sp").id,
            "city_id": self.env.ref("l10n_br_base.city_3550308").id,
            "zip": "01311-000",
            "street_name": "Avenida Paulista",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "37.402.925/0001-79",
            "l10n_br_ie_code": "078.016.350.838",
            "tax_framework": "3",
            "profit_calculation": "presumed",
            "is_industry": True,
            "ripi": True,
            "icms_regulation_id": self.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            "legal_nature_id": legal_nature_2062.id,
            "cnae_main_id": fiscal_cnae_3101200.id,
            "piscofins_id": self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            "tax_classification_id": self.env.ref(
                "l10n_br_fiscal.tax_classification_000001"
            ).id,
        }
        company_lp = create_and_configure_br_company(
            self.env,
            data_company_lp,
            self.op_simples_remessa | self.op_bonificacao | self.op_entrada_remessa,
        )
        # Os Impostos por Regime da Empresa chegam às linhas pela Fonte 1 do
        # `operation_line.map_fiscal_taxes`, que lê as tax definitions da
        # EMPRESA. Quem as cria na UI são os onchanges de `tax_icms_id` e
        # `piscofins_id` (`res_company._set_tax_definition`), que não rodam num
        # `create` -- por isso o fixture chama os mesmos métodos, sem repetir
        # aqui os valores das definitions.
        company_lp._onchange_tax_icms_id()
        company_lp._onchange_piscofins_id()

        return company_lp

    def create_empresa_simples_nacional(self):
        # Empresa Simples Nacional
        legal_nature_2062 = self.env["l10n_br_fiscal.legal.nature"].search(
            [("code", "=", "206-2")]
        )
        fiscal_cnae_3101200 = self.env["l10n_br_fiscal.cnae"].search(
            [("code", "=", "3101-2/00")]
        )
        tax_classification_000001 = self.env[
            "l10n_br_fiscal.tax.classification"
        ].search([("code", "=", "000001")])
        data_company_sn = {
            "name": "Empresa Simples Nacional 1",
            "legal_name": "Empresa Simples Nacional 1",
            "country_id": self.env.ref("base.br").id,
            "state_id": self.env.ref("base.state_br_sp").id,
            "city_id": self.env.ref("l10n_br_base.city_3550308").id,
            "zip": "18125-000",
            "street_name": "Rua A",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "69.330.888/0001-27",
            "l10n_br_ie_code": "755.338.250.133",
            "tax_framework": "1",
            "legal_nature_id": legal_nature_2062.id,
            "cnae_main_id": fiscal_cnae_3101200.id,
            "piscofins_id": self.env.ref(
                "l10n_br_fiscal.tax_pis_cofins_simples_nacional"
            ).id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            # Simples Nacional
            "tax_ipi_id": self.env.ref("l10n_br_fiscal.tax_ipi_outros").id,
            "tax_icms_id": self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").id,
            "annual_revenue": "815000.00",
            "tax_classification_id": tax_classification_000001.id,
        }
        company_sn = create_and_configure_br_company(
            self.env,
            data_company_sn,
            self.op_simples_remessa | self.op_bonificacao | self.op_entrada_remessa,
        )
        # Os Impostos do Simples chegam às linhas pela Fonte 1 do
        # `operation_line.map_fiscal_taxes` (tax definitions da EMPRESA): é por
        # aqui que o CSOSN 101 do ICMS entra, já que o Regulamento do ICMS não é
        # consultado fora do Regime Normal, e também o PIS/COFINS do Simples.
        # Na UI quem cria as definitions são os onchanges de `tax_icms_id` e
        # `piscofins_id` (`res_company._set_tax_definition`), que não rodam num
        # `create` -- por isso o fixture chama os mesmos métodos.
        company_sn._onchange_tax_icms_id()
        company_sn._onchange_piscofins_id()

        return company_sn

    @classmethod
    def get_default_groups(cls):
        groups = super().get_default_groups()
        groups |= (
            cls.env.ref("l10n_br_fiscal.group_user")
            | cls.env.ref("l10n_br_fiscal.group_manager")
            | cls.env.ref("stock.group_stock_manager")
        )

        module_l10n_br_nfe = cls.env["ir.module.module"].search(
            [("name", "=", "l10n_br_nfe")]
        )
        if module_l10n_br_nfe and module_l10n_br_nfe.state == "installed":
            groups |= cls.env.ref("l10n_br_nfe.group_manager")

        return groups

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def invoice_pickings(self, pickings):
        """Send the Picking(s) to the invoicing wizard.
        Check the Invoice(s) created and that no other account.move was
        created in the meantime.
        """
        nb_invoice_before = self.env["account.move"].search_count([])
        invoices = create_with_form_inv_onshipping(self.env, pickings)
        self.check_br_invoice_created(pickings, invoices)
        self.assertEqual(
            nb_invoice_before,
            self.env["account.move"].search_count([]) - len(invoices),
            "No other Invoice should have been created.",
        )
        return invoices

    def check_br_invoice_created(self, pickings, invoices):
        """Check the Invoice(s) created from the given Picking(s).
        As assertivas genéricas do módulo pai NÃO são reaproveitadas via
        `super().check_invoice_created`:
        duas delas não valem no Brasil -- o `inv_line.tax_ids` pode ser vazio
        (os impostos da localização ficam em `fiscal_tax_ids`) e a Condição de
        Pagamento na Fatura faz a criação do lançamento falhar
        (`UserError: The entry is not balanced.`) com os dados de teste.
        """
        for picking in pickings:
            self.assertEqual(picking.invoice_state, "invoiced")
            # Verificar os Valores de Preço pois isso é usado na Valorização do
            # Estoque, o metodo do core é chamado pelo botão Validate
            for pck_line in picking.move_ids:
                # No Brasil o caso de Ordens de Entrega que não tem ligação com
                # Pedido de Venda por padrão deve trazer o valor o Preço de Custo
                # e não o de Venda, ex.: Simples Remessa, Remessa p/
                # Industrialiazação e etc, mas o valor informado pelo usuário deve
                # ter prioridade.
                # Os metodos do stock/core alteram o valor p/
                # negativo por isso o abs
                if pck_line.fiscal_operation_id != self.op_entrada_remessa:
                    self.assertEqual(
                        abs(pck_line.price_unit),
                        pck_line.product_id.with_company(
                            pck_line.company_id
                        ).standard_price,
                    )
                # O Campo fiscal_price precisa ser um espelho do price_unit,
                # apesar do onchange p/ preenche-lo sem incluir o compute no campo
                # ele traz o valor do lst_price e falha no teste abaixo
                # TODO - o fiscal_price aqui tbm deve ter um valor negativo ?

            for invoice in invoices:
                self.assertTrue(invoice, "Invoice is not created.")
                self.assertIn(invoice, picking.invoice_ids)
                self.assertIn(picking, invoice.picking_ids)
                # A Fatura é criada com o Parceiro de Faturamento do Picking
                # (`picking._get_partner_to_invoice()`: Endereço de Faturamento
                # do parceiro no stock_picking_invoicing, ou o
                # `partner_invoice_id` do Pedido de Venda quando o Picking vem
                # de um PV -- ver l10n_br_sale_stock, test_05). A
                # assertiva abaixo vale para os parceiros dos fixtures deste
                # common, que não tem Endereço de Faturamento diferente do
                # principal; com Endereço de Faturamento distinto a Fatura sai
                # com ele e o parceiro do Picking vai para o
                # `partner_shipping_id` (`_get_fiscal_partner`).
                self.assertEqual(invoice.partner_id, picking.partner_id)
                self.assertTrue(
                    invoice.fiscal_operation_id,
                    "Mapping fiscal operation on wizard to create invoice fail.",
                )
                self.assertTrue(
                    invoice.fiscal_document_id,
                    "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
                )
                self.assertTrue(
                    invoice.invoice_line_ids, "Error to create invoice line."
                )
                for line in invoice.invoice_line_ids:
                    # Valida presença dos campos principais para o mapeamento Fiscal
                    self.assertTrue(
                        line.fiscal_operation_id, "Missing Fiscal Operation."
                    )
                    self.assertTrue(
                        line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
                    )

                    # Price Unit e Fiscal Price devem ser positivos
                    mv_line_price_unit = picking.move_ids.filtered(
                        lambda mv, line=line: mv.product_id == line.product_id
                    )
                    self.assertTrue(
                        mv_line_price_unit,
                        "Stock Move of the Invoice Line product was not found.",
                    )
                    price_unit_mv_line = mv_line_price_unit.mapped("price_unit")[0]
                    if line.fiscal_operation_id != self.op_entrada_remessa:
                        self.assertEqual(
                            line.price_unit,
                            price_unit_mv_line,
                        )
                        self.assertEqual(
                            line.fiscal_price,
                            price_unit_mv_line,
                        )
                    # TODO: No travis falha o browse aqui
                    #  l10n_br_stock_account/models/stock_invoice_onshipping.py:105
                    #  isso não acontece no caso da empresa de Lucro Presumido
                    #  ou quando é feito o teste apenas instalando os modulos
                    #  l10n_br_account e em seguida o l10n_br_stock_account
                    # self.assertTrue(inv_line.tax_ids,
                    # "Error to map Sale Tax in invoice.line.")
                    self.assertTrue(
                        line.fiscal_tax_ids,
                        "Error to map fiscal_tax_ids in invoice line.",
                    )
                    self.assertTrue(
                        line.ind_final,
                        "Error field ind_final in Invoice Line not None",
                    )
                    # Verifica se o campo tax_ids da Fatura esta igual ao da Separação
                    mv_line = picking.move_ids.filtered(
                        lambda ln, line=line: (
                            ln.product_id == line.product_id
                            and ln.fiscal_operation_id == line.fiscal_operation_id
                        )
                    )
                    self.assertEqual(
                        line.tax_ids,
                        mv_line.tax_ids,
                        "Taxes in invoice lines are different from move lines.",
                    )

    def run_picking_devolution(self, picking):
        picking_devolution = create_with_form_return_picking(self.env, picking)
        return_fiscal_op = picking.fiscal_operation_id.return_fiscal_operation_id
        self.assertEqual(picking_devolution.invoice_state, "2binvoiced")
        self.assertTrue(
            picking_devolution.fiscal_operation_id, "Missing Fiscal Operation."
        )
        self.assertEqual(
            picking_devolution.fiscal_operation_id,
            return_fiscal_op,
            "Wrong Return Fiscal Operation in the Devolution Picking.",
        )
        for line in picking_devolution.move_ids:
            self.assertEqual(line.invoice_state, "2binvoiced")
            # Valida presença dos campos principais para o mapeamento Fiscal
            self.assertTrue(line.fiscal_operation_id, "Missing Fiscal Operation.")
            self.assertEqual(
                line.fiscal_operation_id,
                return_fiscal_op,
                "Wrong Return Fiscal Operation the Devolution Picking.",
            )
            self.assertTrue(
                line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
            )
            self.assertIn(
                line.fiscal_operation_line_id,
                return_fiscal_op.line_ids,
                "Return move line does not belong to the Return Fiscal Operation.",
            )
        self.picking_move_state(picking_devolution)
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")
        return picking_devolution
