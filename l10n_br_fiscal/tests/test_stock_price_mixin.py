# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.models import MetaModel
from odoo.tests import TransactionCase

FAKE_MODEL = "l10n_br_fiscal.test.cost.line"


class TestStockPriceMixin(TransactionCase):
    """Creditability gates and net acquisition cost (cost_unit) of the
    stock price mixin, on a fake line that has nothing but the fiscal line
    mixin and this one.

    The scenarios follow the stock.move tests of l10n_br_stock_account: a
    purchase for industrialization of 800.00 (product_product_6) from a
    regular supplier, which highlights ICMS and adds IPI to the total.
    Expected cost by buyer regime:
    - Lucro Real (industry): total - ICMS - IPI - PIS - COFINS
    - Lucro Presumido (industry): total - ICMS - IPI
    - Simples Nacional: the total, since it takes no credit at all
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls._register_fake_line()

        cls.company_real = cls.env.ref("l10n_br_base.empresa_lucro_real")
        cls.company_presumido = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.company_simples = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        (cls.company_real + cls.company_presumido).write({"is_industry": True})
        cls.product = cls.env.ref("product.product_product_6")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.supplier = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.supplier.tax_framework = "3"  # Normal
        cls.cfop_own_use = cls.env.ref("l10n_br_fiscal.cfop_1556")
        cls.cfop_asset = cls.env.ref("l10n_br_fiscal.cfop_1551")
        cls.cfop_transfer = cls.env.ref("l10n_br_fiscal.cfop_1151")

    @classmethod
    def _register_fake_line(cls):
        """Build the fake line alone in the registry.

        FakeModelLoader reloads every model class of the module, so the
        registry would keep l10n_br_fiscal.document bound to the former
        document mixin, and a module installed later in the same run
        (l10n_br_cte) would extend a mixin that no model inherits anymore.
        """
        from .fake_stock_price_line import FakeStockPriceLine

        registry = cls.env.registry
        cr = cls.env.cr
        cls.addClassCleanup(cls._unregister_fake_line, FakeStockPriceLine)
        with patch.object(cr, "commit"):
            FakeStockPriceLine._build_model(registry, cr)
            registry.setup_models(cr)
            registry.init_models(cr, [FAKE_MODEL], {"module": "l10n_br_fiscal"})
        # the test case compares the attributes of the registry classes with
        # the ones taken in its setUpClass, before the fake line existed
        cls.attrs_before[FAKE_MODEL] = {
            *vars(registry[FAKE_MODEL]),
            "__annotations__",
            "_rec_name",
        }

    @classmethod
    def _unregister_fake_line(cls, fake_class):
        registry = cls.env.registry
        cls.env.flush_all()
        cls.env.invalidate_all()
        registry.models.pop(FAKE_MODEL, None)
        for model in registry.models.values():
            model._inherit_children.discard(FAKE_MODEL)
        module_models = MetaModel.module_to_models["l10n_br_fiscal"]
        if fake_class in module_models:
            module_models.remove(fake_class)
        registry.setup_models(cls.env.cr)

    def _make_line(self, company, qty=1.0, price=800.0, with_operation=True):
        vals = {
            "company_id": company.id,
            "partner_id": self.supplier.id,
            "product_id": self.product.id,
            "uom_id": self.product.uom_id.id,
            "quantity": qty,
            "price_unit": price,
        }
        if with_operation:
            vals.update(
                {
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "fiscal_operation_line_id": self.fiscal_operation_line.id,
                }
            )
        model = self.env[FAKE_MODEL].with_company(company)
        return model.create(vals)

    def _assert_no_credit(self, line):
        self.assertFalse(line.icms_tax_is_creditable)
        self.assertFalse(line.ipi_tax_is_creditable)
        self.assertFalse(line.pis_tax_is_creditable)
        self.assertFalse(line.cofins_tax_is_creditable)

    # ------------------------------------------------------------------
    # BUYER regime
    # ------------------------------------------------------------------

    def test_regime_lucro_real(self):
        """Lucro Real industry: every derivable domain credits."""
        line = self._make_line(self.company_real)
        self.assertTrue(line._is_non_cumulative())
        self.assertTrue(line.icms_tax_is_creditable)
        self.assertTrue(line.ipi_tax_is_creditable)
        self.assertTrue(line.pis_tax_is_creditable)
        self.assertTrue(line.cofins_tax_is_creditable)

    def test_regime_lucro_presumido(self):
        """Cumulative PIS/COFINS never credit, whatever the CST."""
        line = self._make_line(self.company_presumido)
        self.assertFalse(line._is_non_cumulative())
        self.assertTrue(line.icms_tax_is_creditable)
        self.assertTrue(line.ipi_tax_is_creditable)
        self.assertFalse(line.pis_tax_is_creditable)
        self.assertFalse(line.cofins_tax_is_creditable)

    def test_regime_simples_buyer(self):
        """A Simples Nacional buyer takes no credit (LC 123/2006, art. 23)."""
        line = self._make_line(self.company_simples)
        self._assert_no_credit(line)

    def test_ipi_needs_an_industry(self):
        """A trader does not credit IPI: it stays in the cost."""
        self.company_presumido.write({"is_industry": False, "ripi": False})
        line = self._make_line(self.company_presumido)
        self.assertFalse(line.ipi_tax_is_creditable)
        # ICMS is not gated by the industry:
        self.assertTrue(line.icms_tax_is_creditable)
        self.assertGreater(line.ipi_value, 0)
        self.assertAlmostEqual(
            line.cost_unit, line.fiscal_amount_total - line.icms_value, places=2
        )

    def test_ipi_for_a_company_assimilated_to_industry(self):
        """The RIPI flag alone (assimilated to industry) opens the IPI credit."""
        self.company_presumido.write({"is_industry": False, "ripi": True})
        line = self._make_line(self.company_presumido)
        self.assertTrue(line.ipi_tax_is_creditable)

    def test_piscofins_regime_wins_over_profit_calculation(self):
        """A Lucro Real company listed in art. 10 of Lei 10.833/2003 stays
        cumulative: the PIS/COFINS record decides, not the profit regime."""
        line = self._make_line(self.company_real)
        self.assertTrue(line.pis_tax_is_creditable)
        self.assertGreater(line.pis_value, 0)
        self.assertGreater(line.cofins_value, 0)
        cost_non_cumulative = line.cost_unit

        self.company_real.piscofins_id = self.env.ref(
            "l10n_br_fiscal.tax_pis_cofins_columativo"
        )

        self.assertEqual(self.company_real.profit_calculation, "real")
        self.assertFalse(line._is_non_cumulative())
        self.assertFalse(line.pis_tax_is_creditable)
        self.assertFalse(line.cofins_tax_is_creditable)
        # ICMS and IPI are untouched by the PIS/COFINS regime:
        self.assertTrue(line.icms_tax_is_creditable)
        self.assertTrue(line.ipi_tax_is_creditable)
        self.assertAlmostEqual(
            line.cost_unit,
            cost_non_cumulative + line.pis_value + line.cofins_value,
            places=2,
        )

    def test_profit_calculation_is_the_fallback(self):
        """Without a PIS/COFINS record, the profit regime decides."""
        self.company_real.piscofins_id = False
        line = self._make_line(self.company_real)
        self.assertTrue(line._is_non_cumulative())
        self.assertTrue(line.pis_tax_is_creditable)

        self.company_real.profit_calculation = "presumed"

        self.assertFalse(line._is_non_cumulative())
        self.assertFalse(line.pis_tax_is_creditable)
        self.assertFalse(line.cofins_tax_is_creditable)

    # ------------------------------------------------------------------
    # NATURE of the operation (CST)
    # ------------------------------------------------------------------

    def test_cst_nature_gate(self):
        """With regime and destination allowing it, the CST has the last say."""
        line = self._make_line(self.company_real)
        self.assertTrue(line._resolve_tax_creditability("icms"))

        line.icms_cst_id.default_creditable_tax = False

        self.assertFalse(line._resolve_tax_creditability("icms"))
        # Only the ICMS CST changed:
        self.assertTrue(line._resolve_tax_creditability("pis"))

    def test_tax_without_general_credit_is_never_derived(self):
        """ICMS ST, ISSQN and IRPJ have no general input credit."""
        line = self._make_line(self.company_real)
        self.assertTrue(line._resolve_tax_creditability("icms"))
        self.assertFalse(line._resolve_tax_creditability("icmsst"))
        self.assertFalse(line._resolve_tax_creditability("issqn"))
        self.assertFalse(line._resolve_tax_creditability("irpj"))

    # ------------------------------------------------------------------
    # DESTINATION of the goods (CFOP)
    # ------------------------------------------------------------------

    def test_own_use_destination_vetoes_every_credit(self):
        """Own use and consumption recovers nothing on the acquisition."""
        line = self._make_line(self.company_real)
        self.assertTrue(line.icms_tax_is_creditable)

        line.cfop_id = self.cfop_own_use

        self._assert_no_credit(line)
        self.assertAlmostEqual(
            line.cost_unit, line.fiscal_amount_total / line.quantity, places=2
        )

    def test_fixed_asset_destination_vetoes_every_credit(self):
        """A fixed asset keeps the tax in the cost of the asset."""
        line = self._make_line(self.company_real)
        self.assertTrue(line.icms_tax_is_creditable)

        line.cfop_id = self.cfop_asset

        self._assert_no_credit(line)

    def test_unrestricted_destination_keeps_the_credit(self):
        """The destination gate is a veto, never a permission."""
        line = self._make_line(self.company_real)
        line.cfop_id = self.cfop_transfer
        self.assertEqual(line._creditable_tax_destination_gates(), {})
        self.assertTrue(line.icms_tax_is_creditable)
        self.assertTrue(line.pis_tax_is_creditable)

    # ------------------------------------------------------------------
    # Simples Nacional supplier
    # ------------------------------------------------------------------

    def test_simples_supplier_without_transferred_credit(self):
        """A Simples supplier highlights no ICMS, so none is credited, while
        PIS/COFINS follow the buyer regime (ADI SRF 15/2007)."""
        self.supplier.tax_framework = "1"
        line = self._make_line(self.company_real)
        self.assertFalse(line.icms_tax_is_creditable)
        self.assertTrue(line.pis_tax_is_creditable)
        self.assertTrue(line.cofins_tax_is_creditable)

    def test_simples_supplier_with_transferred_credit(self):
        """CSOSN 101/201 states a credit, and only then ICMS is credited."""
        self.supplier.tax_framework = "1"
        line = self._make_line(self.company_real)
        self.assertFalse(line.icms_tax_is_creditable)

        line.icmssn_credit_value = 50.0

        self.assertTrue(line.icms_tax_is_creditable)

    # ------------------------------------------------------------------
    # Shared decision with the fiscal document line
    # ------------------------------------------------------------------

    def test_stored_flags_follow_the_shared_decision(self):
        """The stored flags and the fiscal line map come from one rule."""
        scenarios = (
            (self.company_real, None),
            (self.company_presumido, None),
            (self.company_simples, None),
            (self.company_real, self.cfop_own_use),
            (self.company_real, self.cfop_asset),
        )
        for company, cfop in scenarios:
            line = self._make_line(company)
            if cfop:
                line.cfop_id = cfop
            stored = line._get_stock_cost_tax_map()
            self.assertEqual(stored, line._get_tax_creditability_map())
            self.assertEqual(
                stored,
                {
                    domain: "credit" if line[f"{domain}_tax_is_creditable"] else "cost"
                    for domain in ("icms", "ipi", "pis", "cofins")
                },
            )

    # ------------------------------------------------------------------
    # cost_unit
    # ------------------------------------------------------------------

    def test_cost_unit_by_regime(self):
        """cost_unit = fiscal total minus what each regime may credit."""
        line_real = self._make_line(self.company_real)
        self.assertGreater(line_real.icms_value, 0)
        self.assertGreater(line_real.ipi_value, 0)
        expected_real = (
            line_real.fiscal_amount_total
            - line_real.icms_value
            - line_real.ipi_value
            - line_real.pis_value
            - line_real.cofins_value
        )
        self.assertAlmostEqual(line_real.cost_unit, expected_real, places=2)

        line_presumido = self._make_line(self.company_presumido)
        expected_presumido = (
            line_presumido.fiscal_amount_total
            - line_presumido.icms_value
            - line_presumido.ipi_value
        )
        self.assertAlmostEqual(line_presumido.cost_unit, expected_presumido, places=2)

        line_simples = self._make_line(self.company_simples)
        self.assertGreater(line_simples.fiscal_amount_total, 0)
        self.assertAlmostEqual(
            line_simples.cost_unit, line_simples.fiscal_amount_total, places=2
        )

    def test_cost_unit_is_per_unit(self):
        """The net cost of the line is divided by its quantity."""
        line = self._make_line(self.company_real, qty=4.0, price=200.0)
        net_total = (
            line.fiscal_amount_total
            - line.icms_value
            - line.ipi_value
            - line.pis_value
            - line.cofins_value
        )
        self.assertAlmostEqual(line.cost_unit, net_total / 4.0, delta=0.01)

    def test_manual_override_keeps_the_tax_in_the_cost(self):
        """Unchecking a derived flag keeps that tax in the cost."""
        line = self._make_line(self.company_presumido)
        net = line.cost_unit
        self.assertGreater(line.icms_value, 0)

        line.icms_tax_is_creditable = False

        self.assertAlmostEqual(line.cost_unit, net + line.icms_value, places=2)

    def test_freight_insurance_other_toggles(self):
        """Freight, insurance and other costs are in the fiscal total; the
        toggles decide whether they stay in the inventory cost."""
        line = self._make_line(self.company_simples)  # no credit noise
        cost_without = line.cost_unit
        line.write(
            {"freight_value": 30.0, "insurance_value": 20.0, "other_value": 10.0}
        )
        with_costs = line.cost_unit
        self.assertGreater(with_costs, cost_without)

        line.freight_value_to_stock = False
        self.assertAlmostEqual(line.cost_unit, with_costs - 30.0, places=2)
        line.insurance_value_to_stock = False
        self.assertAlmostEqual(line.cost_unit, with_costs - 50.0, places=2)
        line.other_value_to_stock = False
        self.assertAlmostEqual(line.cost_unit, with_costs - 60.0, places=2)

    def test_withholding_is_added_back(self):
        """A withholding is a financial obligation, not a smaller cost."""
        line = self._make_line(self.company_simples)  # no credit noise
        total_before = line.fiscal_amount_total
        cost_before = line.cost_unit

        line.amount_tax_withholding = 70.0

        # The withholding does leave the fiscal total...
        self.assertAlmostEqual(line.fiscal_amount_total, total_before - 70.0, places=2)
        # ...but not the acquisition cost.
        self.assertAlmostEqual(line.cost_unit, cost_before, places=2)

    def test_csosn_credit_reduces_the_cost_of_a_regular_buyer(self):
        """The CSOSN 101/201 credit reduces the cost of a non Simples buyer
        buying for industrialization (LC 123/2006, art. 23, par. 1)."""
        line = self._make_line(self.company_presumido)
        base = line.cost_unit

        line.icmssn_credit_value = 50.0

        self.assertAlmostEqual(line.cost_unit, base - 50.0, places=2)

    def test_csosn_credit_ignored_for_a_simples_buyer(self):
        """A Simples buyer takes no credit, the CSOSN one included."""
        line = self._make_line(self.company_simples)
        base = line.cost_unit

        line.icmssn_credit_value = 50.0

        self.assertAlmostEqual(line.cost_unit, base, places=2)

    def test_csosn_credit_only_for_resale_or_industry(self):
        """Own use is outside art. 23, par. 1: the CSOSN credit stays out."""
        line = self._make_line(self.company_presumido)
        line.cfop_id = self.cfop_own_use
        base = line.cost_unit

        line.icmssn_credit_value = 50.0

        self.assertAlmostEqual(line.cost_unit, base, places=2)

    def test_no_cost_without_operation_line(self):
        """Without a fiscal operation line there is no cost to derive."""
        line = self._make_line(self.company_real, with_operation=False)
        self.assertFalse(line.fiscal_operation_line_id)
        self.assertGreater(line.fiscal_amount_total, 0)
        self.assertEqual(line.cost_unit, 0)

    def test_no_cost_without_quantity(self):
        """The cost quantity comes from _get_cost_unit_qty, the hook the
        consumers override, and a zero quantity divides nothing."""
        line = self._make_line(self.company_real)
        self.assertGreater(line.cost_unit, 0)

        with patch.object(type(line), "_get_cost_unit_qty", return_value=0.0):
            line._compute_cost_unit()

        self.assertEqual(line.cost_unit, 0)
