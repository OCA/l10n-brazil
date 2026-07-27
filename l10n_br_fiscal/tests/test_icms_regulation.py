# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import TransactionCase, tagged

from ..constants.fiscal import FINAL_CUSTOMER_NO, FINAL_CUSTOMER_YES, TAX_DOMAIN_ICMS
from .tools import load_fiscal_fixture_files


@tagged("icms")
class TestICMSRegulation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)

        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.company = cls.env.ref("base.main_company")
        cls.product = cls.env.ref("product.product_product_1")
        cls.nbm = cls.env["l10n_br_fiscal.nbm"]
        cls.icms_regulation = cls.env.ref("l10n_br_fiscal.tax_icms_regulation")

        cls.sc_state_id = cls.env.ref("base.state_br_sc")
        cls.sp_state_id = cls.env.ref("base.state_br_sp")
        cls.venda_operation_line_id = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        cls.ncm_48191000_id = cls.env.ref("l10n_br_fiscal.ncm_48191000")
        cls.ncm_energia_id = cls.env.ref("l10n_br_fiscal.ncm_27160000")
        # Dedicated NCM (not used by demo data) so a tax definition can be
        # attached to it in the tests below without impacting other tests.
        cls.ncm_test_id = cls.env["l10n_br_fiscal.ncm"].create(
            {"code": "9999.99.99", "name": "NCM Teste ind_final"}
        )

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

    def _create_ncm_specific_ind_final_yes_definition(self):
        """Create a tax definition restricted to a specific NCM that only
        applies to final consumer operations (ind_final = Yes), while the
        generic SC -> SC tax definitions (ind_final Yes = 17%, No = 12%)
        remain available for every other NCM.

        This reproduces the scenario fixed by commit a6a586bac5: before the
        fix, ``_build_map_tax_def_domain`` did not filter by ``ind_final``,
        so this NCM-specific definition was returned by the domain search
        for *any* ``ind_final`` value. Since it only matches
        ``ind_final = Yes``, requesting the tax for ``ind_final = No``
        ended up with an empty result instead of falling back to the
        generic 12% definition.
        """
        return self.env["l10n_br_fiscal.tax.definition"].create(
            {
                "icms_regulation_id": self.icms_regulation.id,
                "state_from_id": self.sc_state_id.id,
                "state_to_ids": [Command.set([self.sc_state_id.id])],
                "ncm_ids": [Command.set([self.ncm_test_id.id])],
                "ind_final": FINAL_CUSTOMER_YES,
                "is_taxed": True,
                "is_debit_credit": True,
                "custom_tax": True,
                "tax_id": self.env.ref("l10n_br_fiscal.tax_icms_18").id,
                "cst_id": self.env.ref("l10n_br_fiscal.cst_icms_00").id,
                "tax_group_id": self.env.ref("l10n_br_fiscal.tax_group_icms").id,
                "state": "approved",
            }
        )

    def test_icms_sc_sc_ind_final_yes_ncm_specific(self):
        self._create_ncm_specific_ind_final_yes_definition()
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sc_state_id,
            ncm_id=self.ncm_test_id,
            ind_final=FINAL_CUSTOMER_YES,
        )
        self.assertEqual(tax_icms.percent_amount, 18.00)

    def test_icms_sc_sc_ind_final_no_ncm_specific_fallback_to_generic(self):
        self._create_ncm_specific_ind_final_yes_definition()
        tax_icms = self.find_icms_tax(
            in_state_id=self.sc_state_id,
            out_state_id=self.sc_state_id,
            ncm_id=self.ncm_test_id,
            ind_final=FINAL_CUSTOMER_NO,
        )
        self.assertEqual(tax_icms.percent_amount, 12.00)

    def find_icms_tax(self, in_state_id, out_state_id, ncm_id, ind_final):
        self.partner.state_id = in_state_id
        self.company.partner_id.l10n_br_ie_code = False
        self.company.l10n_br_ie_code = False
        self.company.state_id = out_state_id
        self.product.ncm_id = ncm_id

        tax_icms, _ = self.icms_regulation.map_tax(
            company=self.company,
            partner=self.partner,
            product=self.product,
            nbm=self.nbm,
            operation_line=self.venda_operation_line_id,
            ind_final=ind_final,
        )
        return tax_icms.filtered(lambda t: t.tax_domain == TAX_DOMAIN_ICMS)
