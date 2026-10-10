# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import TransactionCase

from ..constants.fiscal import FISCAL_TAX_ID_FIELDS, TAX_VALUE_FIELDS
from .tools import load_fiscal_fixture_files


class TestImportedDocumentTaxAmounts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_6")
        cls.uom = cls.env.ref("uom.product_uom_unit")
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.ipi_tax = cls.env.ref("l10n_br_fiscal.tax_ipi_6_5")
        cls.icms_tax = cls.env.ref("l10n_br_fiscal.tax_icms_18")
        cls.cofins_wh_tax = cls.env.ref("l10n_br_fiscal.tax_cofins_wh_3")

    def _create_imported_document(self, tax_values):
        line_values = {
            "name": "Imported purchase line",
            "product_id": self.product.id,
            "uom_id": self.uom.id,
            "quantity": 1,
            "price_unit": 210.0,
            "fiscal_operation_type": "in",
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
        }
        line_values.update(tax_values)
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type.id,
                "document_serie": "1",
                "document_number": "4909",
                "issuer": "partner",
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_type": "in",
                "imported_document": True,
                "fiscal_line_ids": [Command.create(line_values)],
            }
        )

    def test_ipi_from_the_file_reaches_the_document_total(self):
        document = self._create_imported_document(
            {
                "ipi_tax_id": self.ipi_tax.id,
                "ipi_base": 210.0,
                "ipi_percent": 6.5,
                "ipi_value": 13.65,
            }
        )
        line = document.fiscal_line_ids
        self.assertEqual(line.ipi_value, 13.65)
        self.assertEqual(line.amount_tax_not_included, 13.65)
        self.assertEqual(line.amount_tax_included, 0.0)
        self.assertEqual(line.fiscal_amount_tax, 13.65)
        self.assertEqual(document.amount_ipi_value, 13.65)
        self.assertEqual(document.fiscal_amount_tax, 13.65)
        self.assertEqual(
            document.fiscal_amount_total, document.fiscal_amount_untaxed + 13.65
        )

    def test_icms_from_the_file_stays_inside_the_price(self):
        document = self._create_imported_document(
            {
                "icms_tax_id": self.icms_tax.id,
                "icms_base": 210.0,
                "icms_percent": 18.0,
                "icms_value": 37.8,
            }
        )
        line = document.fiscal_line_ids
        self.assertEqual(line.amount_tax_included, 37.8)
        self.assertEqual(line.amount_tax_not_included, 0.0)
        self.assertEqual(line.fiscal_amount_tax, 0.0)
        self.assertEqual(document.fiscal_amount_tax, 0.0)
        self.assertEqual(document.fiscal_amount_total, document.fiscal_amount_untaxed)

    def test_tax_values_from_the_file_are_not_recomputed(self):
        document = self._create_imported_document(
            {
                "ipi_tax_id": self.ipi_tax.id,
                "ipi_base": 210.0,
                "ipi_percent": 9.75,
                "ipi_value": 20.48,
            }
        )
        line = document.fiscal_line_ids
        self.assertEqual(line.ipi_percent, 9.75)
        self.assertEqual(line.ipi_value, 20.48)
        self.assertEqual(line.amount_tax_not_included, 20.48)

    def test_editing_an_imported_tax_value_updates_the_total(self):
        document = self._create_imported_document(
            {
                "ipi_tax_id": self.ipi_tax.id,
                "ipi_base": 210.0,
                "ipi_percent": 6.5,
                "ipi_value": 13.65,
            }
        )
        line = document.fiscal_line_ids
        line.write({"ipi_value": 20.0})
        self.assertEqual(line.amount_tax_not_included, 20.0)
        self.assertEqual(line.fiscal_amount_tax, 20.0)
        self.assertEqual(document.fiscal_amount_tax, 20.0)

    def test_a_withheld_tax_from_the_file_lands_on_its_own_total(self):
        """Withholding does not raise the note total: it is retained from the payment,
        so it belongs to amount_tax_withholding and to neither of the other two."""
        document = self._create_imported_document(
            {
                "cofins_wh_tax_id": self.cofins_wh_tax.id,
                "cofins_wh_base": 210.0,
                "cofins_wh_percent": 3.0,
                "cofins_wh_value": 6.3,
            }
        )
        line = document.fiscal_line_ids
        self.assertEqual(line.amount_tax_withholding, 6.3)
        self.assertEqual(line.amount_tax_included, 0.0)
        self.assertEqual(line.amount_tax_not_included, 0.0)
        self.assertEqual(
            document.fiscal_amount_total, document.fiscal_amount_untaxed - 6.3
        )

    def test_every_line_tax_field_has_a_value_field(self):
        line_fields = self.env["l10n_br_fiscal.document.line"]._fields
        for tax_field in FISCAL_TAX_ID_FIELDS:
            tax_domain = tax_field[: -len("_tax_id")]
            self.assertIn(tax_domain, TAX_VALUE_FIELDS)
            self.assertIn(TAX_VALUE_FIELDS[tax_domain], line_fields)
