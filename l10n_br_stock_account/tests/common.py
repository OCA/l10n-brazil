# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.stock_picking_invoicing.tests.common import (
    TestStockPickingInvoicingCommon,
)
from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_pck_backorder,
    create_with_form_return_picking,
)

from .tools import (
    create_and_configure_br_company,
    create_br_journal_and_set_fiscal_ops,
    create_with_form_br_res_partner,
    create_with_form_br_stock_picking,
)


class TestBrPickingInvoicingCommon(TestStockPickingInvoicingCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Add main company to test user to access demo data from other modules
        cls.env.user.company_ids |= cls.env.ref("base.main_company")
        cls.get_default_groups()

        # Operação Fiscais comuns em todas as empresas
        cls.op_simples_remessa = cls.env["l10n_br_fiscal.operation"].search(
            [("name", "=", "Simples Remessa")]
        )
        cls.op_bonificacao = cls.env["l10n_br_fiscal.operation"].search(
            [("name", "=", "Bonificação")]
        )
        cls.op_entrada_remessa = cls.env["l10n_br_fiscal.operation"].search(
            [("name", "=", "Entrada de Remessa")]
        )

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

        # Partners usados nos testes, um principal e outro Endereço de Entrega
        data_res_partner = {
            "name": "Cliente 2 -SP - Simples Nacional",
            "legal_name": "Cliente 2 SN - SP",
            "country_id": cls.env.ref("base.br"),
            "state_id": cls.env.ref("base.state_br_sp"),
            "city_id": cls.env.ref("l10n_br_base.city_3550308"),
            "zip": "18125-000",
            "street_name": "Rua A",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "12.046.835/0001-61",
            "l10n_br_ie_code": "887.273.429.152",
            "fiscal_profile_id": cls.env.ref(
                "l10n_br_fiscal.partner_fiscal_profile_snc"
            ),
        }
        cls.partner_br_stock_1 = create_with_form_br_res_partner(
            cls.env, data_res_partner
        )

        data_res_partner_delivery_address = {
            "name": "Cliente 2 - SP - Endereço Entrega",
            "legal_name": "Cliente 2 - SP - Endereço Entrega",
            "country_id": cls.env.ref("base.br"),
            "state_id": cls.env.ref("base.state_br_sp"),
            "city_id": cls.env.ref("l10n_br_base.city_3550308"),
            "zip": "04583-120",
            "street_name": "Rua B",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "96.660.336/0001-50",
            "l10n_br_ie_code": "811.510.100.755",
            "fiscal_profile_id": cls.env.ref(
                "l10n_br_fiscal.partner_fiscal_profile_snc"
            ),
            # Informações dos Contatos
            "company_type": "person",
            "type": "delivery",
            "parent_id": cls.partner_br_stock_1,
        }
        cls.partner_br_stock_1_delivery_address = create_with_form_br_res_partner(
            cls.env, data_res_partner_delivery_address
        )
        cls.partner_br_stock_1_delivery_address.type = "delivery"

        # Dados comuns usados nos Pickings
        picking_out_vals = {
            "partner_id": cls.partner_br_stock_1,
            "picking_type_id": cls.picking_type_out,
            "fiscal_operation_id": cls.op_simples_remessa,
            "company_id": cls.env.company,
        }

        picking_out_vals_delivery_address = picking_out_vals | {
            "partner_id": cls.partner_br_stock_1_delivery_address
        }

        move_vals_1 = [
            {
                "product_id": cls.product_storable_1,
                "product_uom_qty": 2,
                "fiscal_operation_id": cls.op_simples_remessa,
            }
        ]
        move_vals_2 = [
            {
                "product_id": cls.product_storable_2,
                "product_uom_qty": 2,
            }
        ]
        move_vals_3 = [
            {
                "product_id": cls.product_storable_1,
                "product_uom_qty": 2,
                "fiscal_operation_id": cls.op_bonificacao,
            }
        ]

        # Picking Out Empresa principal do testes company_1_data
        cls.picking_out_br_1 = create_with_form_br_stock_picking(
            cls.env, picking_out_vals, move_vals_1 + move_vals_2 + move_vals_3
        )
        # No Form não está sendo possível incluir a OP Bonificação
        cls.picking_out_br_1.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        cls.picking_out_br_2 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_2.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        cls.picking_out_br_3 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals_delivery_address,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_3.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        cls.picking_out_br_4 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_4.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        cls.picking_out_br_5 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals_delivery_address,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_5.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        cls.picking_out_br_6 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_6.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        # Empresa Lucro Real
        legal_nature_2062 = cls.env["l10n_br_fiscal.legal.nature"].search(
            [("code", "=", "206-2")]
        )
        fiscal_cnae_3101200 = cls.env["l10n_br_fiscal.cnae"].search(
            [("code", "=", "3101-2/00")]
        )
        data_company_lp = {
            "name": "Empresa Lucro Presumido 1",
            "legal_name": "Empresa Lucro Presumido 1",
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_sp").id,
            "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
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
            "icms_regulation_id": cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            "legal_nature_id": legal_nature_2062.id,
            "cnae_main_id": fiscal_cnae_3101200.id,
            "piscofins_id": cls.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            "tax_classification_id": cls.env.ref(
                "l10n_br_fiscal.tax_classification_000001"
            ).id,
        }
        cls.company_lp = create_and_configure_br_company(
            cls.env, data_company_lp, cls.fiscal_ops
        )

        cls.picking_type_out_lp = cls.env["stock.picking.type"].search(
            [
                ("company_id", "=", cls.company_lp.id),
                ("code", "=", "outgoing"),
            ],
            limit=1,
        )
        picking_out_vals_lp = picking_out_vals | {
            "company_id": cls.company_lp,
            "picking_type_id": cls.picking_type_out_lp,
        }
        cls.picking_out_br_lp_1 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals_lp,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_lp_1.move_ids[2].fiscal_operation_id = cls.op_bonificacao

        # Empresa Simples Nacional
        tax_classification_000001 = cls.env["l10n_br_fiscal.tax.classification"].search(
            [("code", "=", "000001")]
        )
        data_company_sn = {
            "name": "Empresa Simples Nacional 1",
            "legal_name": "Empresa Simples Nacional 1",
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_sp").id,
            "city_id": cls.env.ref("l10n_br_base.city_3550308").id,
            "zip": "18125-000",
            "street_name": "Rua A",
            "street_number": "1",
            "district": "Bela Vista",
            "vat": "69.330.888/0001-27",
            "l10n_br_ie_code": "755.338.250.133",
            "tax_framework": "1",
            "legal_nature_id": legal_nature_2062.id,
            "cnae_main_id": fiscal_cnae_3101200.id,
            "piscofins_id": cls.env.ref(
                "l10n_br_fiscal.tax_pis_cofins_simples_nacional"
            ).id,
            "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
            # Simples Nacional
            "tax_ipi_id": cls.env.ref("l10n_br_fiscal.tax_ipi_outros").id,
            "tax_icms_id": cls.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito").id,
            "annual_revenue": "815000.00",
            "tax_classification_id": tax_classification_000001.id,
        }
        cls.company_sn = create_and_configure_br_company(
            cls.env, data_company_sn, cls.fiscal_ops
        )

        cls.picking_type_out_sn = cls.env["stock.picking.type"].search(
            [
                ("company_id", "=", cls.company_sn.id),
                ("code", "=", "outgoing"),
            ],
            limit=1,
        )
        picking_out_vals_sn = picking_out_vals | {
            "company_id": cls.company_sn,
            "picking_type_id": cls.picking_type_out_sn,
        }
        cls.picking_out_br_sn_1 = create_with_form_br_stock_picking(
            cls.env,
            picking_out_vals_sn,
            move_vals_1 + move_vals_2 + move_vals_3,
        )
        cls.picking_out_br_sn_1.move_ids[2].fiscal_operation_id = cls.op_bonificacao

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

    def create_invoice_wizard(self, pickings):
        return create_with_form_inv_onshipping(self.env, pickings)

    def return_picking_wizard(self, picking):
        return create_with_form_return_picking(self.env, picking)

    def create_backorder_wizard(self, picking):
        return create_with_form_pck_backorder(self.env, picking)

    def check_br_invoice_created(self, invoices, pickings):
        for picking in pickings:
            self.assertEqual(picking.state, "done")
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
                self.assertEqual(picking.invoice_state, "invoiced")
                self.assertIn(invoice, picking.invoice_ids)
                self.assertIn(picking, invoice.picking_ids)
                self.assertEqual(invoice.partner_id, picking.partner_id)
                self.assertTrue(
                    invoice.fiscal_operation_id,
                    "Mapping fiscal operation on wizard to create invoice fail.",
                )
                self.assertTrue(
                    invoice.fiscal_document_id,
                    "Mapping Fiscal Documentation_id on wizard to create invoice fail.",
                )
                assert invoice.invoice_line_ids, "Error to create invoice line."
                for line in invoice.invoice_line_ids:
                    # Valida presença dos campos principais para o mapeamento Fiscal
                    self.assertTrue(
                        line.fiscal_operation_id, "Missing Fiscal Operation."
                    )
                    self.assertTrue(
                        line.fiscal_operation_line_id, "Missing Fiscal Operation Line."
                    )

                    # Price Unit e Fiscal Price devem ser positivos
                    price_unit_mv_line = picking.move_ids.filtered(
                        lambda mv, line=line: mv.product_id == line.product_id
                    ).mapped("price_unit")[0]
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
                    assert (
                        line.ind_final
                    ), "Error field ind_final in Invoice Line not None"
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
                return_fiscal_op.line_ids,
                line.fiscal_operation_line_id,
                "Wrong Return Line Fiscal Operation the Devolution Picking.",
            )
        self.picking_move_state(picking_devolution)
        self.assertEqual(picking_devolution.state, "done", "Change state fail.")
        return picking_devolution
