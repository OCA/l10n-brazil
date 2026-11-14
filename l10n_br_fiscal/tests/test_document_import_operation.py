# Copyright (C) 2026 - TODAY KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import TransactionCase


class TestImportOperationTotals(TransactionCase):
    """Totals of an import entry (CFOP 3xxx) with IPI.

    In an import entry the taxes that stay inside the price (II, ICMS, PIS,
    COFINS) are added back to the total by _add_fields_to_amount, while the
    IPI (tax group with tax_include = False) reaches it through
    amount_tax_not_included. The IPI must be counted exactly once.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_6")
        cls.uom = cls.env.ref("uom.product_uom_unit")
        cls.document_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.cfop_import = cls.env.ref("l10n_br_fiscal.cfop_3102")
        cls.ii_tax = cls.env.ref("l10n_br_fiscal.tax_ii_10")
        cls.ipi_tax = cls.env.ref("l10n_br_fiscal.tax_ipi_15")
        cls.icms_tax = cls.env.ref("l10n_br_fiscal.tax_icms_17")

    def _create_document(self, imported, line_values=None):
        values = {
            "name": "Import entry line",
            "product_id": self.product.id,
            "uom_id": self.uom.id,
            "quantity": 1,
            "price_unit": 1000.0,
            "fiscal_operation_type": "in",
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
            "cfop_id": self.cfop_import.id,
        }
        values.update(line_values or {})
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type.id,
                "document_serie": "1",
                "document_number": "4504",
                "issuer": "partner",
                "partner_id": self.partner.id,
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_type": "in",
                "imported_document": imported,
                "fiscal_line_ids": [Command.create(values)],
            }
        )

    def _assert_ipi_counted_once(self, line):
        self.assertTrue(line.ipi_value)
        inside_the_price = (
            line.ii_value
            + line.icms_value
            + line.pis_value
            + line.cofins_value
            + line.ii_customhouse_charges
        )
        self.assertAlmostEqual(line.fiscal_amount_tax, line.ipi_value, places=2)
        self.assertAlmostEqual(
            line.fiscal_amount_total,
            line.price_gross + inside_the_price + line.ipi_value,
            places=2,
            msg="the IPI must be added to the import entry total exactly once",
        )
        document = line.document_id
        self.assertAlmostEqual(
            document.fiscal_amount_total, line.fiscal_amount_total, places=2
        )

    def test_typed_import_entry_counts_the_ipi_once(self):
        document = self._create_document(imported=False)
        line = document.fiscal_line_ids
        line.write(
            {
                "cfop_id": self.cfop_import.id,
                "ii_tax_id": self.ii_tax.id,
                "ipi_tax_id": self.ipi_tax.id,
                "icms_tax_id": self.icms_tax.id,
            }
        )
        self._assert_ipi_counted_once(line)

    def test_imported_import_entry_counts_the_ipi_once(self):
        document = self._create_document(
            imported=True,
            line_values={
                "ii_tax_id": self.ii_tax.id,
                "ii_base": 1000.0,
                "ii_percent": 10.0,
                "ii_value": 100.0,
                "ipi_tax_id": self.ipi_tax.id,
                "ipi_base": 1100.0,
                "ipi_percent": 15.0,
                "ipi_value": 165.0,
                "icms_tax_id": self.icms_tax.id,
                "icms_base": 1524.10,
                "icms_percent": 17.0,
                "icms_value": 259.10,
            },
        )
        self._assert_ipi_counted_once(document.fiscal_line_ids)
