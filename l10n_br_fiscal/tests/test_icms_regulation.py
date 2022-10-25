from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..constants.fiscal import FINAL_CUSTOMER_NO, FINAL_CUSTOMER_YES


@tagged("icms")
class TestICMSRegulation(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env.ref("l10n_br_base.res_partner_akretion")
        self.company = self.env.ref("base.main_company")
        self.product = self.env.ref("product.product_product_1")
        self.nbm = self.env["l10n_br_fiscal.nbm"]
        self.icms_regulation = self.env.ref("l10n_br_fiscal.tax_icms_regulation")

        self.sc_state_id = self.env.ref("base.state_br_sc")
        self.sp_state_id = self.env.ref("base.state_br_sp")
        self.venda_operation_line_id = self.env.ref("l10n_br_fiscal.fo_venda_venda")
        self.ncm_48191000_id = self.env.ref("l10n_br_fiscal.ncm_48191000")
        self.ncm_energia_id = self.env.ref("l10n_br_fiscal.ncm_27160000")

    def test_icms_sc_sc_ind_final_yes_default(self):
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sc_state_id,
            ncm_id=self.ncm_48191000_id,
            ind_final=FINAL_CUSTOMER_YES,
        )
        self.assertEqual(tax_icms.percent_amount, 17.00)

    def test_icms_sc_sc_ind_final_no_default(self):
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sc_state_id,
            ncm_id=self.ncm_48191000_id,
            ind_final=FINAL_CUSTOMER_NO,
        )
        self.assertEqual(tax_icms.percent_amount, 12.00)

    def test_icms_sc_sc_ind_final_yes_ncm_energia(self):
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sc_state_id,
            ncm_id=self.ncm_energia_id,
            ind_final=FINAL_CUSTOMER_YES,
        )
        self.assertEqual(tax_icms.percent_amount, 25.00)

    def test_icms_sc_sp_ind_final_yes_default(self):
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sp_state_id,
            ncm_id=self.ncm_48191000_id,
            ind_final=FINAL_CUSTOMER_YES,
        )
        self.assertEqual(tax_icms.percent_amount, 12.00)

    def find_icms_tax(self, in_state_id, out_state_id, ncm_id, ind_final):

        self.partner.state_id = in_state_id
        self.company.state_id = out_state_id
        self.product.ncm_id = ncm_id

        tax_icms = self.icms_regulation.map_tax_icms(
            company=self.company,
            partner=self.partner,
            product=self.product,
            nbm=self.nbm,
            operation_line=self.venda_operation_line_id,
            ind_final=ind_final,
        )
        return tax_icms
