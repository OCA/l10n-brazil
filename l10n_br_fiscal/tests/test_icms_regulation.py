from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("icms")
class TestICMSRegulation(TransactionCase):
    def setUp(self):
        super().setUp()

        self.env["l10n_br_fiscal.tax.definition"].create(
            {
                "icms_regulation_id": self.env.ref(
                    "l10n_br_fiscal.tax_icms_regulation"
                ).id,
                "ncms": "7323.99.00",
                "state_from_id": self.env.ref("base.state_br_sp").id,
                "state_to_ids": [(6, 0, [self.env.ref("base.state_br_mg").id])],
                "is_taxed": True,
                "is_debit_credit": True,
                "tax_id": self.env.ref("l10n_br_fiscal.tax_icmsst_57").id,
                "tax_group_id": self.env.ref("l10n_br_fiscal.tax_group_icmsst").id,
                "state": "approved",
            }
        )

        self.nbm = self.env["l10n_br_fiscal.nbm"]
        self.cst_icms_00 = self.env.ref("l10n_br_fiscal.cst_icms_00")
        self.cst_icms_10 = self.env.ref("l10n_br_fiscal.cst_icms_10")
        self.icms_regulation = self.env.ref("l10n_br_fiscal.tax_icms_regulation")
        self.venda_operation_line_id = self.env.ref("l10n_br_fiscal.fo_venda_venda")

    def test_icms_imported_with_st(self):
        self.partner = self.env.ref("l10n_br_base.res_partner_cliente9_mg")
        self.company = self.env.ref("base.main_company")
        self.product = self.env.ref("product.product_product_9")
        tax_icms = self.find_icms_tax()
        self.assertEqual(tax_icms.cst_out_id, self.cst_icms_10)

    def test_icms_imported_without_st(self):
        self.partner = self.env.ref("l10n_br_base.res_partner_cliente7_rs")
        self.company = self.env.ref("base.main_company")
        self.product = self.env.ref("product.product_product_9")
        tax_icms = self.find_icms_tax()
        self.assertEqual(tax_icms.cst_out_id, self.cst_icms_00)

    def find_icms_tax(self):
        return self.icms_regulation.map_tax_icms(
            company=self.company,
            partner=self.partner,
            product=self.product,
            nbm=self.nbm,
            operation_line=self.venda_operation_line_id,
        )
