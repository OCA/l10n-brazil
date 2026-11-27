# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestImportedLineValues(TransactionCase):
    """Values declared in a fiscal file survive the recompute of an imported line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Supplier of flour",
                "state_id": cls.env.ref("base.state_br_mg").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Wheat flour", "uom_id": cls.uom_kg.id, "uom_po_id": cls.uom_kg.id}
        )
        cls.company = cls.env.company
        cls.company.state_id = cls.env.ref("base.state_br_sp")
        cls.company.country_id = cls.env.ref("base.br")
        cls.document = cls._create_document(imported=True)
        cls.line = cls._create_line(cls.document)

    @classmethod
    def _create_document(cls, imported):
        return cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "imported_document": imported,
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _create_line(cls, document, **values):
        vals = {
            "document_id": document.id,
            "name": "FLOUR T1 BAG 25KG",
            "quantity": 2.0,
            "price_unit": 100.0,
            "uom_id": cls.uom_unit.id,
            "partner_uom_code": "SC",
            "partner_cfop_id": cls.env.ref("l10n_br_fiscal.cfop_6102").id,
        }
        vals.update(values)
        return cls.env["l10n_br_fiscal.document.line"].create(vals)

    def test_matching_a_product_keeps_the_declared_values(self):
        """Setting the internal product must not let the computes replace what
        the file declared: description, quantity, price and unit."""
        self.line.product_id = self.product
        self.assertEqual(self.line.name, "FLOUR T1 BAG 25KG")
        self.assertEqual(self.line.quantity, 2.0)
        self.assertEqual(self.line.price_unit, 100.0)
        self.assertEqual(self.line.uom_id, self.uom_unit)

    def test_matching_a_product_keeps_the_taxation_unit_and_values(self):
        """uTrib, vUnTrib and qTrib are independent of the matched product."""
        line = self._create_line(
            self.document,
            uot_id=self.uom_kg.id,
            fiscal_price=4.0,
            fiscal_quantity=50.0,
        )
        line.product_id = self.product
        line.write({"quantity": 5.0, "price_unit": 40.0})
        self.assertEqual(line.uot_id, self.uom_kg)
        self.assertEqual(line.fiscal_price, 4.0)
        self.assertEqual(line.fiscal_quantity, 50.0)

    def test_matching_a_product_does_not_give_a_unit_the_file_did_not_bring(self):
        """The unit the supplier declared matched no unit: the line has none, and the
        product that is matched to it does not fill one."""
        self.product.uot_id = self.env.ref("uom.product_uom_ton")
        line = self._create_line(self.document, uom_id=False)
        self.assertFalse(line.uom_id)
        line.product_id = self.product
        self.assertFalse(line.uom_id)
        self.assertFalse(line.uot_id)
        # control: a line that was not imported takes the unit of the product
        typed = self._create_line(
            self._create_document(imported=False), uom_id=False, partner_uom_code=False
        )
        typed.product_id = self.product
        self.assertEqual(typed.uom_id, self.uom_kg)

    def test_matching_a_product_without_ncm_keeps_the_declared_ncm(self):
        """The NCM of the file is what the books of an inbound document carry,
        even when the product matched has none."""
        # the NCM table is loaded in a reduced mode in tests: bring a classification
        ncm = self.env["l10n_br_fiscal.ncm"].create(
            {"name": "NCM of the test", "code": "9999.99.99"}
        )
        line = self._create_line(
            self.document, ncm_id=ncm.id, partner_ncm_code="99999999"
        )
        self.assertFalse(self.product.ncm_id)
        line.product_id = self.product
        self.assertEqual(line.ncm_id, ncm)

        # control: on a line that was not imported the product rules
        typed = self._create_line(self._create_document(imported=False), ncm_id=ncm.id)
        typed.product_id = self.product
        self.assertFalse(typed.ncm_id)

    def test_matching_a_product_does_not_bring_the_ncm_of_the_product(self):
        ncm_product = self.env["l10n_br_fiscal.ncm"].create(
            {"name": "NCM of the product", "code": "8888.88.88"}
        )
        self.product.ncm_id = ncm_product
        line = self._create_line(self.document, partner_ncm_code="99999999")
        line.product_id = self.product
        self.assertFalse(line.ncm_id)

    def test_total_follows_the_gross_total_declared(self):
        """Quantity times price can miss the cents of the file: the total of the
        line follows the declared value."""
        line = self._create_line(
            self.document,
            quantity=3.0,
            price_unit=3.33,
            partner_price_gross=10.0,
        )
        self.assertEqual(line.price_gross, 10.0)
        self.assertEqual(line.amount_fiscal, 10.0)
        self.assertEqual(line.fiscal_amount_total, 10.0)
        self.assertEqual(self.line.price_gross, 200.0)

    def test_total_goes_back_to_the_calculation_when_a_person_edits(self):
        line = self._create_line(
            self.document,
            quantity=3.0,
            price_unit=3.33,
            partner_price_gross=10.0,
        )
        # the same values written back change nothing
        line.write({"quantity": 3.0, "price_unit": 3.33})
        self.assertEqual(line.partner_price_gross, 10.0)
        # the review of the line converts the values on purpose
        line.with_context(import_review_apply=True).quantity = 5.0
        self.assertEqual(line.partner_price_gross, 10.0)
        line.quantity = 4.0
        self.assertFalse(line.partner_price_gross)
        self.assertEqual(line.price_gross, 13.32)

    def test_the_operation_line_survives_the_product_of_the_review(self):
        """The operation line of an imported line is the one of its CFOP: matching a
        product, for which the operation defines no line, must not take it away, or
        the line stops adding to the financial total of the document."""
        operation = self.env.ref("l10n_br_fiscal.fo_venda")
        operation_line = self.env.ref("l10n_br_fiscal.fo_venda_revenda")
        document = self._create_document(imported=True)
        document.fiscal_operation_id = operation
        line = self._create_line(
            document,
            fiscal_operation_id=operation.id,
            fiscal_operation_line_id=operation_line.id,
        )
        self.assertEqual(line.fiscal_operation_line_id, operation_line)
        line.write({"product_id": self.product.id})
        self.assertEqual(line.fiscal_operation_line_id, operation_line)
        self.assertTrue(line.financial_total)

    def test_manual_cfop_survives_the_operation_remap(self):
        """A CFOP chosen by a person on an imported line is a decision, not a
        suggestion: recomputing the mapping must not overwrite it."""
        cfop_1102 = self.env.ref("l10n_br_fiscal.cfop_1102")
        cfop_2102 = self.env.ref("l10n_br_fiscal.cfop_2102")
        # a CFOP the mapping below can never produce
        cfop_1556 = self.env.ref("l10n_br_fiscal.cfop_1556")
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-CFOP",
                "name": "Purchase (manual CFOP test)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
                "state": "approved",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Purchase (manual CFOP test)",
                "cfop_internal_id": cfop_1102.id,
                "cfop_external_id": cfop_2102.id,
                "state": "approved",
            }
        )
        control = self._create_line(self.document, product_id=self.product.id)
        control.fiscal_operation_id = operation
        # control: the mapping does remap the CFOP of an imported line
        self.assertFalse(control.cfop_manual)
        self.assertIn(control.cfop_id, cfop_1102 | cfop_2102)

        self.line.product_id = self.product
        self.line.cfop_id = cfop_1556
        self.assertTrue(self.line.cfop_manual)
        self.line.fiscal_operation_id = operation
        self.assertEqual(self.line.cfop_id, cfop_1556)

    def test_classification_of_the_file_stays_when_the_mapping_is_empty(self):
        """An operation line that maps no classification must not clear the one
        the file declared."""
        classification = self.env["l10n_br_fiscal.tax.classification"].create(
            {"name": "Classification of the file", "code": "000001"}
        )
        self.company.tax_classification_id = False
        operation = self.env.ref("l10n_br_fiscal.fo_compras")
        operation_line = operation.line_ids.filtered(
            lambda line: not line.tax_classification_id
        )[:1]
        self.assertTrue(operation_line)
        self.line.tax_classification_id = classification
        self.line.fiscal_operation_line_id = operation_line
        self.assertEqual(self.line.tax_classification_id, classification)

    def test_cfop_warning_on_line(self):
        """The declared CFOP is checked against the real geography."""
        # issuer MG x company SP with an intrastate CFOP -> warn
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_5102")
        self.assertTrue(self.line.cfop_warning)
        # interstate CFOP -> consistent
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_6102")
        self.assertFalse(self.line.cfop_warning)
        # foreign trade CFOP with both parties in Brazil -> warn
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_3102")
        self.assertTrue(self.line.cfop_warning)
        # foreign issuer with a foreign trade CFOP -> consistent
        self.partner.country_id = self.env.ref("base.us")
        self.partner.state_id = False
        self.assertFalse(self.line.cfop_warning)
