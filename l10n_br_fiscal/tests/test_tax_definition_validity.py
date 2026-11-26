# Copyright 2026 Escodoo - Cristiano Mafra Junior
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged

from .tools import load_fiscal_fixture_files


@tagged("post_install", "-at_install")
class TestTaxDefinitionValidity(TransactionCase):
    """Tests that ``map_tax_definition`` actually enforces the
    ``date_start``/``date_end`` validity window against ``reference_date``,
    instead of only being called with it (which the ``reference_date=False``
    assertions elsewhere in the test suite do not exercise).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.product = cls.env.ref("product.product_product_6")
        cls.tax_group_icms = cls.env.ref("l10n_br_fiscal.tax_group_icms")
        cls.tax_icms_12 = cls.env.ref("l10n_br_fiscal.tax_icms_12")

    def _create_definition(self, **date_values):
        # No fiscal_operation_line_id/company_id/cfop_id/icms_regulation_id
        # is set on purpose: those uniqueness constraints would otherwise
        # require dedicated fixtures unrelated to what is being tested here.
        return self.env["l10n_br_fiscal.tax.definition"].create(
            {
                "type_in_out": "out",
                "tax_group_id": self.tax_group_icms.id,
                "custom_tax": True,
                "tax_id": self.tax_icms_12.id,
                "is_taxed": True,
                "is_debit_credit": True,
                "state": "approved",
                **date_values,
            }
        )

    def _map_tax_definition(self, definition, **kwargs):
        # Mirrors how document_line_mixin._compute_fiscal_tax_ids always
        # passes concrete (possibly empty) recordsets, never None, for
        # these optional criteria.
        return definition.map_tax_definition(
            self.company,
            self.partner,
            self.product,
            city_taxation_code=self.env["l10n_br_fiscal.city.taxation.code"],
            national_taxation_code=self.env["l10n_br_fiscal.national.taxation.code"],
            service_type=self.env["l10n_br_fiscal.service.type"],
            **kwargs,
        )

    def test_map_tax_definition_no_dates_always_matches(self):
        definition = self._create_definition()
        result = self._map_tax_definition(definition)
        self.assertEqual(result, definition)

    def test_map_tax_definition_default_now_excludes_expired(self):
        definition = self._create_definition(
            date_end=fields.Datetime.now() - timedelta(days=1)
        )
        result = self._map_tax_definition(definition)
        self.assertFalse(result)

    def test_map_tax_definition_default_now_excludes_not_yet_valid(self):
        definition = self._create_definition(
            date_start=fields.Datetime.now() + timedelta(days=1)
        )
        result = self._map_tax_definition(definition)
        self.assertFalse(result)

    def test_map_tax_definition_reference_date_within_validity_matches(self):
        definition = self._create_definition(
            date_start=fields.Datetime.now() + timedelta(days=10),
            date_end=fields.Datetime.now() + timedelta(days=20),
        )
        result = self._map_tax_definition(
            definition, reference_date=definition.date_start + timedelta(days=1)
        )
        self.assertEqual(result, definition)

    def test_map_tax_definition_reference_date_outside_validity_excludes(self):
        definition = self._create_definition(
            date_start=fields.Datetime.now() + timedelta(days=10),
            date_end=fields.Datetime.now() + timedelta(days=20),
        )
        result = self._map_tax_definition(
            definition, reference_date=definition.date_end + timedelta(days=1)
        )
        self.assertFalse(result)
