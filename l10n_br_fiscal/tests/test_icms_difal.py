# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged

from ..constants.fiscal import (
    FINAL_CUSTOMER_YES,
    NFE_IND_IE_DEST_1,
    NFE_IND_IE_DEST_9,
)
from ..constants.icms import ICMS_ORIGIN_DEFAULT
from .tools import load_fiscal_fixture_files


@tagged("post_install", "-at_install")
class TestIcmsDifal(TransactionCase):
    """ICMS DIFAL on interstate sales of 100.00 from a company in SP.

    Rates from the ICMS regulation data: SP to MG and RJ 12%, SP to PE 7%;
    internal MG 18%, PE 20.5%, RJ 22%; FCP MG 2%, RJ 4%.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company.icms_regulation_id = cls.env.ref(
            "l10n_br_fiscal.tax_icms_regulation"
        )
        profile_non_taxpayer = cls.env.ref("l10n_br_fiscal.partner_fiscal_profile_pfnc")
        profile_taxpayer = cls.env.ref("l10n_br_fiscal.partner_fiscal_profile_cnt")
        cls.mg_non_taxpayer = cls._create_partner(
            "MG", NFE_IND_IE_DEST_9, profile_non_taxpayer
        )
        cls.pe_non_taxpayer = cls._create_partner(
            "PE", NFE_IND_IE_DEST_9, profile_non_taxpayer
        )
        cls.rj_non_taxpayer = cls._create_partner(
            "RJ", NFE_IND_IE_DEST_9, profile_non_taxpayer
        )
        cls.mg_taxpayer = cls._create_partner("MG", NFE_IND_IE_DEST_1, profile_taxpayer)
        cls.tax_icms_7 = cls.env.ref("l10n_br_fiscal.tax_icms_7")
        cls.tax_icms_12 = cls.env.ref("l10n_br_fiscal.tax_icms_12")
        cls.tax_icmsfcp_2 = cls.env.ref("l10n_br_fiscal.tax_icmsfcp_2")
        cls.tax_icmsfcp_4 = cls.env.ref("l10n_br_fiscal.tax_icmsfcp_4")

    @classmethod
    def _create_partner(cls, state_code, ind_ie_dest, profile):
        return cls.env["res.partner"].create(
            {
                "name": f"DIFAL {state_code} {ind_ie_dest}",
                "is_company": ind_ie_dest != NFE_IND_IE_DEST_9,
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref(f"base.state_br_{state_code.lower()}").id,
                "fiscal_profile_id": profile.id,
                "ind_ie_dest": ind_ie_dest,
            }
        )

    def _compute(self, taxes, partner):
        return taxes.compute_taxes(
            company=self.company,
            partner=partner,
            product=self.env.ref("product.product_product_12"),
            price_unit=100.0,
            quantity=1.0,
            uom_id=self.env.ref("uom.product_uom_unit"),
            fiscal_price=100.0,
            fiscal_quantity=1.0,
            uot_id=self.env.ref("uom.product_uom_unit"),
            discount_value=0.0,
            insurance_value=0.0,
            other_value=0.0,
            freight_value=0.0,
            ii_customhouse_charges=0.0,
            ii_iof_value=0.0,
            ncm=self.env.ref("l10n_br_fiscal.ncm_72132000"),
            nbs=self.env["l10n_br_fiscal.nbs"],
            nbm=self.env["l10n_br_fiscal.nbm"],
            cest=self.env["l10n_br_fiscal.cest"],
            operation_line=self.env.ref("l10n_br_fiscal.fo_venda_venda"),
            cfop=self.env.ref("l10n_br_fiscal.cfop_6102"),
            icms_origin=ICMS_ORIGIN_DEFAULT,
            icms_cst_id=self.env.ref("l10n_br_fiscal.cst_icms_00"),
            ind_final=FINAL_CUSTOMER_YES,
        )["taxes"]

    def test_difal_taxpayer_final_consumer(self):
        """Taxpayer buying for its own use: no DIFAL on the sale.

        The recipient pays its own DIFAL (LC 87/1996, art. 4, par. 2, I).
        Only the interstate ICMS remains: 100.00 x 12% = 12.00.
        """
        self.assertEqual(self.mg_taxpayer.ind_ie_dest, NFE_IND_IE_DEST_1)
        taxes = self._compute(self.tax_icms_12, self.mg_taxpayer)
        self.assertAlmostEqual(taxes["icms"]["tax_value"], 12.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_base"], 0.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 0.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_origin_value"], 0.00, places=2)

    def test_difal_company_without_icms_regulation(self):
        """Company without ICMS regulation: no error and no DIFAL.

        Only the interstate ICMS remains: 100.00 x 12% = 12.00.
        """
        self.company.icms_regulation_id = False
        taxes = self._compute(self.tax_icms_12, self.mg_non_taxpayer)
        self.assertAlmostEqual(taxes["icms"]["tax_value"], 12.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 0.00, places=2)

    def test_difal_non_taxpayer_inside_base(self):
        """Non-taxpayer in MG: single base grossed up with rate and FCP.

        With FCP: base = 100.00 / (1 - 0.18 - 0.02) = 125.00;
        DIFAL = 125.00 x (18% - 12%) = 7.50; FCP = 125.00 x 2% = 2.50.
        Without FCP: base = 100.00 / (1 - 0.18) = 121.951... = 121.95;
        DIFAL = 121.95 x 6% = 7.317 = 7.32.
        """
        taxes = self._compute(
            self.tax_icms_12 | self.tax_icmsfcp_2, self.mg_non_taxpayer
        )
        self.assertAlmostEqual(taxes["icms"]["tax_value"], 12.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_perc"], 18.0, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_base"], 125.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 7.50, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_origin_value"], 0.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_sharing_percent"], 100.0, places=2)
        self.assertAlmostEqual(taxes["icmsfcp"]["base"], 125.00, places=2)
        self.assertAlmostEqual(taxes["icmsfcp"]["tax_value"], 2.50, places=2)

        taxes = self._compute(self.tax_icms_12, self.mg_non_taxpayer)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_base"], 121.95, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 7.32, places=2)

    def test_difal_non_taxpayer_simple_base(self):
        """Non-taxpayer in PE: the operation value is the base.

        Base = 100.00; DIFAL = 100.00 x (20.5% - 7%) = 13.50.
        """
        taxes = self._compute(self.tax_icms_7, self.pe_non_taxpayer)
        self.assertAlmostEqual(taxes["icms"]["tax_value"], 7.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_perc"], 20.5, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_base"], 100.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 13.50, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_origin_value"], 0.00, places=2)

    def test_difal_non_taxpayer_simple_base_with_fcp(self):
        """Non-taxpayer in RJ: FCP does not change the simple base.

        Base = 100.00; DIFAL = 100.00 x (22% - 12%) = 10.00;
        FCP = 100.00 x 4% = 4.00.
        """
        taxes = self._compute(
            self.tax_icms_12 | self.tax_icmsfcp_4, self.rj_non_taxpayer
        )
        self.assertAlmostEqual(taxes["icms"]["icms_dest_perc"], 22.0, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_base"], 100.00, places=2)
        self.assertAlmostEqual(taxes["icms"]["icms_dest_value"], 10.00, places=2)
        self.assertAlmostEqual(taxes["icmsfcp"]["base"], 100.00, places=2)
        self.assertAlmostEqual(taxes["icmsfcp"]["tax_value"], 4.00, places=2)
