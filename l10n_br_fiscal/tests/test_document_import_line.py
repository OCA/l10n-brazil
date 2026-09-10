# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestDocumentImportLine(TransactionCase):
    """Review states and persisted de-para on imported document lines."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_ton = cls.env.ref("uom.product_uom_ton")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Fornecedor Farinha",
                "state_id": cls.env.ref("base.state_br_mg").id,
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Farinha de Trigo Tipo 1",
                "uom_id": cls.uom_kg.id,
                "uom_po_id": cls.uom_kg.id,
            }
        )
        cls.company = cls.env.company
        cls.company.state_id = cls.env.ref("base.state_br_sp")
        cls.company.country_id = cls.env.ref("base.br")
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": cls.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                # fiscal_operation_type is a stored related of the operation
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_compras").id,
                "imported_document": True,
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
            }
        )
        # A line faithfully imported: supplier sells bags (SC) of 25kg.
        cls.line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "name": "FARINHA TRIGO T1 SC 25KG",
                "quantity": 2.0,
                "price_unit": 100.0,
                "uom_id": cls.uom_unit.id,
                # the importer persists the unit code declared in the file
                "partner_uom_code": "SC",
                "partner_cfop_id": cls.env.ref("l10n_br_fiscal.cfop_6102").id,
            }
        )

    def test_init_and_aggregate_states(self):
        line_matched = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "name": "Linha ja casada",
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 10.0,
                "uom_id": self.uom_kg.id,
            }
        )
        self.document._init_import_states()
        self.assertEqual(self.line.import_state, "pending")
        self.assertEqual(line_matched.import_state, "matched")
        self.assertEqual(self.document.import_state, "pending")
        self.assertEqual(self.document.import_pending_count, 2)

        line_matched.product_id = self.product
        line_matched._apply_import_depara()
        self.assertEqual(self.document.import_state, "in_progress")

        self.line.product_id = self.product
        self.line._apply_import_depara()
        self.assertEqual(self.document.import_state, "resolved")
        self.assertEqual(self.document.import_pending_count, 0)

    def test_apply_depara_math_and_snapshot(self):
        """Quantity times factor, price divided by it: the total is
        invariant, and the supplier values are preserved as a snapshot."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.assertEqual(self.line.import_state, "resolved")
        # snapshot of the supplier nomenclature: the unit code stays the one
        # declared by the counterparty, never the internal unit
        self.assertEqual(self.line.partner_quantity, 2.0)
        self.assertEqual(self.line.partner_price_unit, 100.0)
        self.assertEqual(self.line.partner_uom_code, "SC")
        # converted to the internal unit, total preserved
        self.assertEqual(self.line.uom_id, self.uom_kg)
        self.assertEqual(self.line.quantity, 50.0)
        self.assertEqual(self.line.price_unit, 4.0)
        self.assertAlmostEqual(
            self.line.quantity * self.line.price_unit,
            self.line.partner_quantity * self.line.partner_price_unit,
            places=2,
        )
        # the de-para learning is persisted on the supplier info, with the
        # price already expressed in the internal unit (4/kg, not 100/bag)
        self.assertTrue(self.line.import_supplierinfo_id)
        self.assertEqual(self.line.import_supplierinfo_id.partner_id, self.partner)
        self.assertAlmostEqual(self.line.import_supplierinfo_id.price, 4.0, places=2)
        self.assertIn(
            self.line.import_supplierinfo_id,
            self.product.product_tmpl_id.seller_ids,
        )

    def test_apply_depara_is_idempotent_on_snapshot(self):
        """Re-applying the de-para (e.g. fixing a wrong factor) must convert
        from the original supplier snapshot, not compound the conversion."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.line._apply_import_depara(uom=self.uom_ton, factor=0.025)
        self.assertEqual(self.line.partner_quantity, 2.0)
        self.assertAlmostEqual(self.line.quantity, 0.05, places=4)
        self.assertAlmostEqual(self.line.price_unit, 4000.0, places=2)

    def test_apply_depara_factor_back_to_one_restores_declared_values(self):
        """A wrong factor is undone by re-applying the de-para with 1.0: the
        line goes back to exactly what the counterparty declared."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.line._apply_import_depara(uom=self.uom_kg, factor=1.0)
        # quantity AND unit price are checked separately on purpose: the line
        # total is algebraically invariant to the factor, so it proves nothing
        self.assertEqual(self.line.quantity, 2.0)
        self.assertEqual(self.line.price_unit, 100.0)
        self.assertEqual(self.line.partner_quantity, 2.0)
        self.assertEqual(self.line.partner_price_unit, 100.0)

    def test_apply_depara_with_unknown_supplier_uom(self):
        """A supplier unit with no internal equivalent (the line lands with
        an empty uom_id) must not convert the line against an empty
        snapshot: quantity and price would be zeroed."""
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "name": "FARINHA TRIGO T1 SC 25KG",
                "quantity": 2.0,
                "price_unit": 100.0,
                "partner_uom_code": "SC",
            }
        )
        self.assertFalse(line.uom_id)
        line._apply_import_depara(product=self.product, uom=self.uom_kg, factor=25.0)
        self.assertEqual(line.partner_uom_code, "SC")
        self.assertEqual(line.partner_quantity, 2.0)
        self.assertEqual(line.partner_price_unit, 100.0)
        self.assertEqual(line.quantity, 50.0)
        self.assertEqual(line.price_unit, 4.0)

    def test_supplierinfo_is_reused_across_imports(self):
        """Importing the same item from the same supplier twice must reuse
        the de-para already learned instead of piling up sellers."""
        self.line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        learned = self.line.import_supplierinfo_id
        second_line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "name": "FARINHA TRIGO T1 SC 25KG",
                "quantity": 4.0,
                "price_unit": 110.0,
                "uom_id": self.uom_unit.id,
                "partner_uom_code": "SC",
            }
        )
        second_line._apply_import_depara(
            product=self.product, uom=self.uom_kg, factor=25.0
        )
        self.assertEqual(second_line.import_supplierinfo_id, learned)
        self.assertEqual(
            len(
                self.env["product.supplierinfo"].search(
                    [
                        ("partner_id", "=", self.partner.id),
                        ("product_id", "=", self.product.id),
                    ]
                )
            ),
            1,
        )
        # the learning follows the last import, in the internal unit
        self.assertAlmostEqual(learned.price, 4.4, places=2)

    def test_manual_cfop_survives_the_operation_remap(self):
        """A CFOP chosen by the user on an imported line is a decision, not a
        suggestion: recomputing the fiscal mapping must not overwrite it."""
        cfop_1102 = self.env.ref("l10n_br_fiscal.cfop_1102")
        cfop_2102 = self.env.ref("l10n_br_fiscal.cfop_2102")
        # a CFOP the mapping below can never produce
        cfop_1556 = self.env.ref("l10n_br_fiscal.cfop_1556")
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-CFOP",
                "name": "Compra (teste de CFOP manual)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
                "state": "approved",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Compra (teste de CFOP manual)",
                "cfop_internal_id": cfop_1102.id,
                "cfop_external_id": cfop_2102.id,
                "state": "approved",
            }
        )
        control = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": self.document.id,
                "name": "Linha sem CFOP escolhido",
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 10.0,
                "uom_id": self.uom_kg.id,
            }
        )
        control.fiscal_operation_id = operation
        # control: the mapping does remap the CFOP of an imported line
        self.assertFalse(control.cfop_manual)
        self.assertIn(control.cfop_id, cfop_1102 | cfop_2102)

        self.line.product_id = self.product
        self.line.cfop_id = cfop_1556
        self.assertTrue(self.line.cfop_manual)
        self.line.fiscal_operation_id = operation
        self.assertEqual(self.line.cfop_id, cfop_1556)

    def test_recompute_guards_preserve_imported_values(self):
        """Setting the internal product on an imported line must not let the
        stored computes overwrite the values imported from the file."""
        self.line.product_id = self.product
        self.assertEqual(self.line.name, "FARINHA TRIGO T1 SC 25KG")
        self.assertEqual(self.line.quantity, 2.0)
        self.assertEqual(self.line.price_unit, 100.0)
        self.assertEqual(self.line.uom_id, self.uom_unit)

    def test_imported_ncm_survives_the_product_match(self):
        """The NCM declared in the file is what the SPED books of an inbound
        document must carry: resolving the line to an internal product whose
        own NCM is empty must not clear it."""
        # the NCM table is loaded in a reduced "demo/test mode", so the test
        # brings its own classification instead of relying on an xmlid
        ncm = self.env["l10n_br_fiscal.ncm"].create(
            {"name": "NCM de teste", "code": "9999.99.99"}
        )
        self.line.ncm_id = ncm
        self.assertFalse(self.product.ncm_id)
        self.line.product_id = self.product
        self.assertEqual(self.line.ncm_id, ncm)

        # control: on a line that was not imported the product still rules
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "partner_id": self.partner.id,
                "company_id": self.company.id,
            }
        )
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Linha digitada",
                "quantity": 1.0,
                "price_unit": 10.0,
                "uom_id": self.uom_kg.id,
                "ncm_id": ncm.id,
            }
        )
        line.product_id = self.product
        self.assertFalse(line.ncm_id)

    def test_suggest_fiscal_operation_in_via_inverse_cfop(self):
        """The inbound operation is suggested through the inverse CFOP of
        the CFOP declared by the counterparty."""
        cfop_6102 = self.env.ref("l10n_br_fiscal.cfop_6102")
        cfop_2102 = self.env.ref("l10n_br_fiscal.cfop_2102")
        cfop_6102.cfop_inverse_id = cfop_2102
        operation = self.env["l10n_br_fiscal.operation"].create(
            {
                "code": "TST-COMPRA",
                "name": "Compra para revenda (teste)",
                "fiscal_operation_type": "in",
                "fiscal_type": "purchase",
                "state": "approved",
            }
        )
        self.env["l10n_br_fiscal.operation.line"].create(
            {
                "fiscal_operation_id": operation.id,
                "name": "Compra para revenda (teste)",
                "cfop_internal_id": self.env.ref("l10n_br_fiscal.cfop_1102").id,
                "cfop_external_id": cfop_2102.id,
                "state": "approved",
            }
        )
        # Several approved operations may reference the inverse CFOP (the
        # core demo data already wires fo_compras to it): the suggestion is
        # the first approved candidate, and it must be an inbound operation
        # whose lines reference the inverse CFOP.
        suggested = self.line._suggest_fiscal_operation_in()
        self.assertTrue(suggested)
        self.assertEqual(suggested.fiscal_operation_type, "in")
        self.assertIn(
            cfop_2102,
            suggested.line_ids.cfop_internal_id
            | suggested.line_ids.cfop_external_id
            | suggested.line_ids.cfop_export_id,
        )
        self.assertEqual(self.document._suggest_fiscal_operation(), suggested)

        # the wizard lookup goes through the same inverse path now
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create({})
        self.assertEqual(
            wizard._find_fiscal_operation("6102", "Compra para revenda (teste)", "in"),
            operation,
        )

    def test_cfop_warning_on_line(self):
        """The declared CFOP is checked against the real geography."""
        # issuer MG x company SP with an intrastate CFOP -> warn
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_5102")
        self.assertTrue(self.line._get_cfop_warning())
        # interstate CFOP -> consistent
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_6102")
        self.assertFalse(self.line._get_cfop_warning())
        # foreign trade CFOP with both parties in Brazil -> warn
        self.line.partner_cfop_id = self.env.ref("l10n_br_fiscal.cfop_3102")
        self.assertTrue(self.line._get_cfop_warning())
        # foreign issuer with a foreign trade CFOP -> consistent
        self.partner.country_id = self.env.ref("base.us")
        self.partner.state_id = False
        self.assertFalse(self.line._get_cfop_warning())
