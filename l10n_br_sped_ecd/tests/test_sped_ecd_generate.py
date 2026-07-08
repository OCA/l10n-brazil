# Copyright 2024 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

# from odoo.addons import l10n_br_sped_ecd
from odoo.tests.common import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class SpedTest(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.fol_sale_with_icms_reduction = cls.env[
            "l10n_br_fiscal.operation.line"
        ].create(
            {
                "name": "Venda com ICMS 12 e Redução de 26,57",
                "ind_ie_dest": "1",
                "cfop_internal_id": cls.env.ref("l10n_br_fiscal.cfop_5101").id,
                "cfop_external_id": cls.env.ref("l10n_br_fiscal.cfop_6101").id,
                "cfop_export_id": cls.env.ref("l10n_br_fiscal.cfop_7101").id,
                "state": "approved",
                "product_type": "04",
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
            }
        )

        cls.pis_tax_definition_empresa_lc = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_pis").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_pis_0_65").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_pis_01").id,
                "state": "approved",
            }
        )

        cls.cofins_tax_definition_empresa_lc = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_cofins").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_cofins_3").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_cofins_01").id,
                "state": "approved",
            }
        )

        cls.cofins_tax_definition_empresa_lc_icms_reduction = cls.env[
            "l10n_br_fiscal.tax.definition"
        ].create(
            {
                "company_id": cls.company_data["company"].id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icms_12_red_26_57").id,
                "cst_id": cls.env.ref("l10n_br_fiscal.cst_icms_20").id,
                "state": "approved",
                "fiscal_operation_line_id": cls.fol_sale_with_icms_reduction.id,
            }
        )

        cls.empresa_lc_document_55_serie_1 = cls.env[
            "l10n_br_fiscal.document.serie"
        ].create(
            {
                "code": "1",
                "name": "Série 1",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "active": True,
            }
        )

        cls.move_out_venda = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )

        cls.env.ref("l10n_br_fiscal.fo_compras").deductible_taxes = True
        cls.move_in_compra_para_revenda = cls.init_invoice(
            "in_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                cls.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="42",
        )

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        if company_name == "company_1_data":
            company_name = "empresa 1 Lucro Presumido"
        else:
            company_name = "empresa 2 Lucro Presumido"
        chart_template = cls.env.ref("l10n_br_coa_generic.l10n_br_coa_generic_template")
        res = super().setup_company_data(
            company_name,
            chart_template,
            tax_framework="3",
            is_industry=True,
            industry_type="00",
            profit_calculation="presumed",
            ripi=True,
            piscofins_id=cls.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo").id,
            icms_regulation_id=cls.env.ref("l10n_br_fiscal.tax_icms_regulation").id,
            cnae_main_id=cls.env.ref("l10n_br_fiscal.cnae_3101200").id,
            document_type_id=cls.env.ref("l10n_br_fiscal.document_55").id,
            **kwargs,
        )
        res["company"].partner_id.state_id = cls.env.ref("base.state_br_sp").id
        chart_template.load_fiscal_taxes()
        return res

    def test_generate_sped(self):
        self.env["l10n_br_sped.mixin"]._flush_registers("ecd")
        file_path = path.join(self.demo_path, "demo_ecd_output.txt")
        declaration = self.env["l10n_br_sped.declaration"].create({})
        # sped_mixin._import_file(file_path, "ecd")
        sped = declaration._generate_sped_text()
        with open(file_path) as f:
            target_content = f.read()
            # print(sped)
            self.assertEqual(sped.strip(), target_content.strip())
        self.assertEqual(
            self.move_out_venda.invoice_line_ids[0].cfop_id.name,
            "Venda de produção do estabelecimento",
        )
