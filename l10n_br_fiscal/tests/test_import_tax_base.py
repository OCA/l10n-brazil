# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from ..constants.fiscal import FINAL_CUSTOMER_NO
from ..constants.icms import ICMS_ORIGIN_DEFAULT
from .tools import load_fiscal_fixture_files

CUSTOMS_VALUE = 101654.28
DECLARED_II = 17999.20


class TestImportTaxBase(TransactionCase):
    """The Import Tax of the declaration has to compose the base of the others.

    Taken from a real import: a line of NCM 8537.10.90, whose product file
    carries II 0%, and a declaration that charged the Import Tax anyway,
    because the tariff of the classification is not zero. The base of the IPI
    came out as the customs value alone, the IPI was short by the tariff over
    the Import Tax, and the ICMS followed it down, since the IPI composes its
    base. On a note that reaches the SEFAZ this is rejection 538 and 528.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.currency = cls.company.currency_id
        cls.taxes = cls.env.ref("l10n_br_fiscal.tax_ii_0") + cls.env.ref(
            "l10n_br_fiscal.tax_ipi_9_75"
        )

    def _kwargs(self, **overrides):
        values = {
            "company": self.company,
            "partner": self.env.ref("l10n_br_base.res_partner_cliente5_pe"),
            "product": self.env.ref("product.product_product_12"),
            "price_unit": CUSTOMS_VALUE,
            "quantity": 1.000,
            "uom_id": self.env.ref("uom.product_uom_unit"),
            "fiscal_price": CUSTOMS_VALUE,
            "fiscal_quantity": 1.000,
            "uot_id": self.env.ref("uom.product_uom_unit"),
            "discount_value": 0.00,
            "insurance_value": 0.00,
            "other_value": 0.00,
            "freight_value": 0.00,
            "ii_customhouse_charges": 0.00,
            "ii_iof_value": 0.00,
            "ncm": self.env.ref("l10n_br_fiscal.ncm_72132000"),
            "nbs": False,
            "nbm": False,
            "cest": False,
            "operation_line": self.env.ref("l10n_br_fiscal.fo_compras_compras"),
            "cfop": self.env.ref("l10n_br_fiscal.cfop_3101"),
            "icmssn_range": False,
            "icms_origin": ICMS_ORIGIN_DEFAULT,
            "ind_final": FINAL_CUSTOMER_NO,
        }
        values.update(overrides)
        return values

    def test_the_declared_import_tax_composes_the_ipi_base(self):
        result = self.taxes.compute_taxes(**self._kwargs(ii_declared_value=DECLARED_II))
        ipi = result["taxes"]["ipi"]
        self.assertEqual(
            self.currency.round(ipi["base"]),
            self.currency.round(CUSTOMS_VALUE + DECLARED_II),
            "the base of the IPI on an import is the customs value plus the "
            "Import Tax the declaration charged",
        )
        self.assertEqual(
            self.currency.round(ipi["tax_value"]),
            self.currency.round((CUSTOMS_VALUE + DECLARED_II) * 0.0975),
        )

    def test_the_declared_import_tax_wins_over_the_product_rate(self):
        result = self.taxes.compute_taxes(**self._kwargs(ii_declared_value=DECLARED_II))
        ii = result["taxes"]["ii"]
        self.assertEqual(self.currency.round(ii["tax_value"]), DECLARED_II)
        self.assertAlmostEqual(
            ii["base"] * ii["percent_amount"] / 100.0,
            DECLARED_II,
            places=2,
            msg="base times rate has to reproduce the amount charged, or the "
            "SEFAZ refuses the note with 528",
        )

    def test_without_a_declaration_the_product_rate_still_rules(self):
        """Contraproof: nothing changes for whoever does not inform a value."""
        result = self.taxes.compute_taxes(**self._kwargs())
        self.assertEqual(self.currency.round(result["taxes"]["ii"]["tax_value"]), 0.00)
        self.assertEqual(
            self.currency.round(result["taxes"]["ipi"]["base"]),
            self.currency.round(CUSTOMS_VALUE),
        )

    def test_a_zero_declaration_is_not_a_declaration(self):
        """An import free of the tax keeps following the product file."""
        result = self.taxes.compute_taxes(**self._kwargs(ii_declared_value=0.00))
        self.assertEqual(
            self.currency.round(result["taxes"]["ipi"]["base"]),
            self.currency.round(CUSTOMS_VALUE),
        )
