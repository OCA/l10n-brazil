# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestCostUnit(TransactionCase):
    """Net acquisition cost (cost_unit) derived from the line CST plus the
    buyer company tax regime (art. 301 RIR/2018, CPC 16).

    Reference invoice: price 800.00 + IPI 26.00 = fiscal total 826.00, with
    ICMS 96.00 highlighted. Expected unit cost by buyer regime:
    - Lucro Real (industry): 826 - ICMS - IPI - PIS - COFINS
    - Lucro Presumido (industry): 826 - ICMS - IPI (cumulative PIS/COFINS
      never credit)
    - Simples Nacional: 826.00 (takes no credit at all)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company_presumido = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company_real = cls.env.ref("l10n_br_base.empresa_lucro_real")
        cls.company_simples = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        # Deterministic regime axes for the IPI gate:
        (cls.company_presumido + cls.company_real).write({"is_industry": True})
        cls.env.user.company_ids += (
            cls.company_presumido + cls.company_real + cls.company_simples
        )

        # A product of its own: switching a category to real time revalues
        # whatever is already in stock, so a demo product would drag the
        # fixture into the test.
        cls.product = cls.env.ref("product.product_product_6").copy(
            {"name": "Net cost product (test)"}
        )
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        # Stated rather than inherited from the demo: the supplier regime is
        # one of the axes these tests exercise.
        cls.supplier.tax_framework = "3"  # Normal
        # The net cost only replaces the move price under perpetual
        # inventory, so the category has to provide it. Switching a category
        # to real time revalues what is already in stock, which needs the
        # valuation accounts in place first.
        account, bridge = (
            cls.env["account.account"].create(
                {
                    "name": name,
                    "code": code,
                    "account_type": "asset_current",
                    "company_id": cls.company_presumido.id,
                }
            )
            for name, code in (
                ("Stock valuation (test)", "TSTCU"),
                ("Stock bridge (test)", "TSTCB"),
            )
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "Stock journal (test)",
                "code": "TSTCJ",
                "type": "general",
                "company_id": cls.company_presumido.id,
            }
        )
        cls.product.categ_id.with_company(cls.company_presumido).write(
            {
                "property_stock_account_input_categ_id": bridge.id,
                "property_stock_account_output_categ_id": bridge.id,
                "property_stock_valuation_account_id": account.id,
                "property_stock_journal": journal.id,
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
            }
        )

    def _make_in_move(self, company, qty=1.0, price=800.0):
        move = (
            self.env["stock.move"]
            .with_company(company)
            .create(
                {
                    "name": self.product.name,
                    "product_id": self.product.id,
                    "product_uom": self.product.uom_id.id,
                    "product_uom_qty": qty,
                    "price_unit": price,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                    "company_id": company.id,
                    "partner_id": self.supplier.id,
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": self.fiscal_operation_line.id,
                }
            )
        )
        return move

    def test_creditable_flags_lucro_real(self):
        """Lucro Real industry: every derivable domain with creditable CST."""
        move = self._make_in_move(self.company_real)
        self.assertTrue(move.icms_tax_is_creditable)
        self.assertTrue(move.ipi_tax_is_creditable)
        self.assertTrue(move.pis_tax_is_creditable)
        self.assertTrue(move.cofins_tax_is_creditable)
        # No general legal input credit - manual only:
        self.assertFalse(move.icmsst_tax_is_creditable)

    def test_creditable_flags_lucro_presumido(self):
        """Presumido: cumulative PIS/COFINS never credit, whatever the CST."""
        move = self._make_in_move(self.company_presumido)
        self.assertTrue(move.icms_tax_is_creditable)
        self.assertTrue(move.ipi_tax_is_creditable)
        self.assertFalse(move.pis_tax_is_creditable)
        self.assertFalse(move.cofins_tax_is_creditable)

    def test_creditable_flags_simples_buyer(self):
        """Simples Nacional buyer takes no credit (LC 123/2006, art. 23)."""
        move = self._make_in_move(self.company_simples)
        self.assertFalse(move.icms_tax_is_creditable)
        self.assertFalse(move.ipi_tax_is_creditable)
        self.assertFalse(move.pis_tax_is_creditable)
        self.assertFalse(move.cofins_tax_is_creditable)

    def test_cost_unit_by_regime(self):
        """cost_unit = fiscal total minus what each regime may credit."""
        move_real = self._make_in_move(self.company_real)
        expected_real = (
            move_real.fiscal_amount_total
            - move_real.icms_value
            - move_real.ipi_value
            - move_real.pis_value
            - move_real.cofins_value
        )
        self.assertGreater(move_real.icms_value, 0)
        self.assertAlmostEqual(move_real.cost_unit, expected_real, places=2)

        move_presumido = self._make_in_move(self.company_presumido)
        expected_presumido = (
            move_presumido.fiscal_amount_total
            - move_presumido.icms_value
            - move_presumido.ipi_value
        )
        self.assertAlmostEqual(move_presumido.cost_unit, expected_presumido, places=2)

        move_simples = self._make_in_move(self.company_simples)
        self.assertAlmostEqual(
            move_simples.cost_unit, move_simples.fiscal_amount_total, places=2
        )

    def test_manual_override_per_line(self):
        """The fiscal user has the last word: unchecking a derived flag
        keeps that tax in the cost (same product, other destination)."""
        move = self._make_in_move(self.company_presumido)
        net = move.cost_unit
        move.icms_tax_is_creditable = False
        self.assertAlmostEqual(move.cost_unit, net + move.icms_value, places=2)

    def test_get_price_unit_opt_in(self):
        """Valuation only switches to the net cost when the company opts in."""
        self.company_presumido.stock_valuation_via_stock_price = False
        move = self._make_in_move(self.company_presumido)
        self.assertFalse(move.valuation_via_stock_price)
        # Opted out means the core price is kept untouched. Asserting only
        # that it differs from cost_unit would hold by construction, since
        # the net cost always differs from the gross one when there is tax.
        self.assertAlmostEqual(move._get_price_unit(), move.price_unit, places=2)

        self.company_presumido.stock_valuation_via_stock_price = True
        move_opted = self._make_in_move(self.company_presumido)
        self.assertTrue(move_opted.valuation_via_stock_price)
        self.assertAlmostEqual(
            move_opted._get_price_unit(), move_opted.cost_unit, places=2
        )
        # And the net cost differs from the raw purchase price:
        self.assertNotEqual(move_opted.cost_unit, move_opted.price_unit)

    def test_ipi_not_creditable_for_non_industry(self):
        """A trader (non-industry) does not credit IPI: it stays in the cost."""
        self.company_presumido.write({"is_industry": False, "ripi": False})
        move = self._make_in_move(self.company_presumido)
        self.assertFalse(move.ipi_tax_is_creditable)
        # ICMS still credits (not gated by industry):
        self.assertTrue(move.icms_tax_is_creditable)
        expected = move.fiscal_amount_total - move.icms_value
        self.assertGreater(move.ipi_value, 0)
        self.assertAlmostEqual(move.cost_unit, expected, places=2)

    def test_freight_insurance_other_toggles(self):
        """Freight/insurance/other are in the fiscal total; the toggles decide
        whether they stay in the inventory cost."""
        move = self._make_in_move(self.company_simples)  # no tax credit noise
        move.write(
            {
                "freight_value": 30.0,
                "insurance_value": 20.0,
                "other_value": 10.0,
            }
        )
        with_costs = move.cost_unit
        # Turning a toggle off removes that component from the cost:
        move.freight_value_to_stock = False
        self.assertAlmostEqual(
            move.cost_unit, with_costs - 30.0 / move.product_uom_qty, places=2
        )
        move.insurance_value_to_stock = False
        move.other_value_to_stock = False
        self.assertAlmostEqual(
            move.cost_unit, with_costs - 60.0 / move.product_uom_qty, places=2
        )

    def test_csosn_credit_reduces_cost_non_simples_buyer(self):
        """The CSOSN 101/201 credit passed on by a Simples supplier reduces
        the cost for a non-Simples buyer (LC 123/2006, art. 23)."""
        move = self._make_in_move(self.company_presumido)
        base = move.cost_unit
        move.icmssn_credit_value = 50.0
        self.assertAlmostEqual(
            move.cost_unit, base - 50.0 / move.product_uom_qty, places=2
        )

    def test_csosn_credit_ignored_for_simples_buyer(self):
        """A Simples buyer takes no credit, so the CSOSN value does not
        reduce its cost."""
        move = self._make_in_move(self.company_simples)
        base = move.cost_unit
        move.icmssn_credit_value = 50.0
        self.assertAlmostEqual(move.cost_unit, base, places=2)

    def test_icms_relief_not_double_counted(self):
        """ICMS relief is already removed from fiscal_amount_total, so
        cost_unit must not subtract it a second time.

        Asserted against the movement of both numbers rather than against
        the total itself: comparing cost_unit to fiscal_amount_total would
        hold whether the relief was counted once, twice or not at all.
        """
        move = self._make_in_move(self.company_presumido)
        total_before = move.fiscal_amount_total
        cost_before = move.cost_unit

        move.icms_relief_value = 40.0

        # The relief leaves the fiscal total once...
        self.assertAlmostEqual(move.fiscal_amount_total, total_before - 40.0, places=2)
        # ...and the cost follows it by that same amount. Subtracting twice
        # would drop the cost by 80.
        self.assertAlmostEqual(
            move.cost_unit,
            cost_before - 40.0 / move.product_uom_qty,
            places=2,
        )

    def test_own_use_destination_blocks_every_credit(self):
        """Own use and consumption recovers nothing on the acquisition.

        No ICMS until 2033 (LC 87/96, art. 33, I), no IPI (RIPI, art. 226)
        and no PIS/COFINS, since it is not an input. A Lucro Real industry
        is used precisely because every regime gate is open for it: what
        closes the credit here is the destination alone.
        """
        move = self._make_in_move(self.company_real)
        self.assertTrue(move.icms_tax_is_creditable)

        move.cfop_id = self.env.ref("l10n_br_fiscal.cfop_1556")

        self.assertFalse(move.icms_tax_is_creditable)
        self.assertFalse(move.ipi_tax_is_creditable)
        self.assertFalse(move.pis_tax_is_creditable)
        self.assertFalse(move.cofins_tax_is_creditable)
        self.assertAlmostEqual(
            move.cost_unit,
            move.fiscal_amount_total / move.product_uom_qty,
            places=2,
        )

    def test_fixed_asset_destination_blocks_every_credit(self):
        """A fixed asset keeps the tax in the cost of the asset.

        There is no IPI credit at all (RIPI, art. 226). ICMS and PIS/COFINS
        are recovered over 48 months, a deferral this module does not
        implement, so leaving them in the cost is the conservative side.
        """
        move = self._make_in_move(self.company_real)
        move.cfop_id = self.env.ref("l10n_br_fiscal.cfop_1551")

        self.assertFalse(move.icms_tax_is_creditable)
        self.assertFalse(move.ipi_tax_is_creditable)
        self.assertFalse(move.pis_tax_is_creditable)
        self.assertFalse(move.cofins_tax_is_creditable)

    def test_transfer_destination_keeps_the_credit(self):
        """The destination gate is a veto, never a permission.

        An interstate transfer between branches states nothing about
        creditability, so the CST decides and the credit survives. Blocking
        everything that is not an explicit purchase would break it.
        """
        move = self._make_in_move(self.company_real)
        move.cfop_id = self.env.ref("l10n_br_fiscal.cfop_1151")
        self.assertTrue(move.icms_tax_is_creditable)

    def test_simples_supplier_grants_no_icms_credit(self):
        """A Simples supplier highlights no ICMS, so none can be credited.

        The buyer is Lucro Real, whose regime gate is open, and the CST on
        the line still says the operation is creditable by nature: what
        removes the credit is the supplier regime with no transferable
        credit on the document.
        """
        self.supplier.tax_framework = "1"  # Simples Nacional
        move = self._make_in_move(self.company_real)

        self.assertFalse(move.icms_tax_is_creditable)
        # PIS and COFINS are taken at the buyer own rates and do not depend
        # on the supplier regime (ADI SRF 15/2007).
        self.assertTrue(move.pis_tax_is_creditable)
        self.assertTrue(move.cofins_tax_is_creditable)

    def test_simples_supplier_with_transferred_credit(self):
        """CSOSN 101/201 states a credit, and only then it is taken."""
        self.supplier.tax_framework = "1"
        move = self._make_in_move(self.company_real)
        move.icmssn_credit_value = 50.0
        self.assertTrue(move.icms_tax_is_creditable)

    def test_withholding_does_not_reduce_the_cost(self):
        """A withholding is a financial obligation, not a smaller cost.

        _compute_fiscal_amounts nets it out of fiscal_amount_total, so the
        cost has to add it back: the goods cost the gross amount (CPC 16,
        item 11) whether or not the buyer withholds tax on payment.
        """
        move = self._make_in_move(self.company_simples)  # no credit noise
        cost_before = move.cost_unit

        move.amount_tax_withholding = 70.0

        self.assertAlmostEqual(move.cost_unit, cost_before, places=2)

    def test_cst_data_defaults(self):
        """Key audited defaults on the CST data (creditability by nature)."""
        ref = self.env.ref
        self.assertTrue(ref("l10n_br_fiscal.cst_icms_00").default_creditable_tax)
        self.assertTrue(ref("l10n_br_fiscal.cst_icms_10").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_icms_51").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_icms_60").default_creditable_tax)
        self.assertTrue(ref("l10n_br_fiscal.cst_icmssn_101").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_icmssn_102").default_creditable_tax)
        self.assertTrue(ref("l10n_br_fiscal.cst_ipi_00").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_ipi_02").default_creditable_tax)
        self.assertTrue(ref("l10n_br_fiscal.cst_pis_50").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_pis_70").default_creditable_tax)
        self.assertFalse(ref("l10n_br_fiscal.cst_cofins_75").default_creditable_tax)
