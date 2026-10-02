# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import date
from pathlib import Path

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from ..wizards.declaration_xml import parse_declaration
from .common import AccountMoveBRCommon

FIXTURE = Path(__file__).parent / "fixtures" / "import_declaration.xml"

# Goods of the fixture, in the order of the declaration: (description, quantity).
ADDITION_1 = [
    ("MERCADORIA 1 DA ADICAO 1", 6.0),
    ("MERCADORIA 2 DA ADICAO 1", 2.0),
    ("MERCADORIA 3 DA ADICAO 1", 8.0),
]
ADDITION_2 = [
    ("MERCADORIA 1 DA ADICAO 2", 2.0),
    ("MERCADORIA 2 DA ADICAO 2", 8.0),
    ("MERCADORIA 3 DA ADICAO 2", 1.0),
    ("MERCADORIA 4 DA ADICAO 2", 2.0),
    ("MERCADORIA 5 DA ADICAO 2", 1.0),
]


@tagged("post_install", "-at_install")
class TestImportDeclarationFile(AccountMoveBRCommon):
    """The wizard fed by the XML of the declaration, addition by addition."""

    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["account.chart.template"].load_fiscal_taxes(
            companies=[cls.company_data["company"]]
        )
        cls.configure_normal_company_taxes()
        # The classification of each addition carries its own rates.
        cls.product_a.ncm_id.sudo().write(
            {
                "tax_ii_id": cls.env.ref("l10n_br_fiscal.tax_ii_12_6").id,
                "tax_ipi_id": cls.env.ref("l10n_br_fiscal.tax_ipi_3_25").id,
            }
        )
        cls.product_b.ncm_id.sudo().write(
            {
                "tax_ii_id": cls.env.ref("l10n_br_fiscal.tax_ii_18").id,
                "tax_ipi_id": cls.env.ref("l10n_br_fiscal.tax_ipi_9_75").id,
            }
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_comercializacao"
        )
        foreign_partner = cls.partner_a.copy(
            {
                "name": "Fornecedor do exterior",
                "legal_name": "Fornecedor do exterior",
                "country_id": cls.env.ref("base.cl").id,
                "state_id": False,
                "vat": False,
                "is_company": True,
            }
        )
        goods = ADDITION_1 + ADDITION_2
        products = [cls.product_a] * len(ADDITION_1) + [cls.product_b] * len(ADDITION_2)
        cls.bill = cls.init_invoice(
            "in_invoice",
            partner=foreign_partner,
            products=products,
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.operation,
            fiscal_operation_lines=[cls.operation_line] * len(goods),
            document_serie="1",
            document_number="0001",
        )
        cls.bill_lines = cls.bill.invoice_line_ids.sorted("id")
        for line, (description, quantity) in zip(cls.bill_lines, goods, strict=True):
            line.write({"name": description, "quantity": quantity, "price_unit": 100.0})

    def _wizard(self):
        wizard = self.env["l10n_br_account.import.declaration.wizard"].create(
            {
                "move_id": self.bill.id,
                "fiscal_operation_id": self.operation.id,
                "fiscal_operation_line_id": self.operation_line.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_date": "2026-07-10 12:00:00",
                "customs_value": 1.0,
                "di_number": "to be replaced",
                "di_date": date(2000, 1, 1),
                "clearance_place": "to be replaced",
                "clearance_state_id": self.env.ref("base.state_br_ac").id,
                "transport_via": "1",
                "exporter_code": "",
                "di_file": base64.b64encode(FIXTURE.read_bytes()),
                "di_filename": FIXTURE.name,
            }
        )
        wizard.action_load_declaration()
        return wizard

    def _addition(self, wizard, number):
        return wizard.addition_ids.filtered(lambda addition: addition.number == number)

    def test_loading_the_file_fills_the_header(self):
        wizard = self._wizard()

        self.assertEqual(wizard.di_number, "2600000001")
        self.assertEqual(wizard.di_date, date(2026, 7, 10))
        self.assertEqual(wizard.clearance_date, date(2026, 7, 10))
        self.assertEqual(wizard.transport_via, "7")
        self.assertEqual(wizard.clearance_state_id, self.env.ref("base.state_br_sp"))
        self.assertEqual(wizard.exporter_code, "EMPRESA DEMONSTRACAO LTDA")
        self.assertAlmostEqual(wizard.customs_value, 800000.00, places=2)
        self.assertAlmostEqual(wizard.ii_value, 141840.00, places=2)
        self.assertAlmostEqual(wizard.ipi_value, 88901.80, places=2)
        self.assertAlmostEqual(wizard.pis_value, 16800.00, places=2)
        self.assertAlmostEqual(wizard.cofins_value, 77200.00, places=2)
        self.assertAlmostEqual(wizard.icms_value, 200000.00, places=2)
        self.assertAlmostEqual(wizard.customhouse_charges, 150.00, places=2)

    def test_loading_the_file_builds_each_addition_with_its_own_rate(self):
        wizard = self._wizard()

        self.assertEqual(wizard.addition_ids.mapped("number"), ["001", "002"])
        first = self._addition(wizard, "001")
        second = self._addition(wizard, "002")
        self.assertEqual(first.ncm_code, "8414.90.20")
        self.assertAlmostEqual(first.customs_value, 40000.00, places=2)
        self.assertAlmostEqual(first.ii_rate, 12.60, places=2)
        self.assertAlmostEqual(first.ii_value, 5040.00, places=2)
        self.assertEqual(first.line_ids, self.bill_lines[:3])
        self.assertEqual(second.ncm_code, "8537.10.90")
        self.assertAlmostEqual(second.customs_value, 760000.00, places=2)
        self.assertAlmostEqual(second.ii_rate, 18.00, places=2)
        self.assertAlmostEqual(second.ii_value, 136800.00, places=2)
        self.assertEqual(second.line_ids, self.bill_lines[3:])
        self.assertFalse(first.unmatched or second.unmatched)
        self.assertFalse(wizard.unclaimed_lines)

    def test_choosing_the_file_on_the_form_loads_it(self):
        wizard = self._wizard()
        wizard.write({"di_number": "typed by hand", "addition_ids": [(5, 0, 0)]})

        wizard._onchange_di_file()

        self.assertEqual(wizard.di_number, "2600000001")
        self.assertEqual(len(wizard.addition_ids), 2)

    def test_the_note_follows_the_addition_of_each_line(self):
        wizard = self._wizard()
        self._align_contributions(wizard)

        wizard.action_generate_document()
        document = wizard.document_id

        lines = document.fiscal_line_ids
        self.assertEqual(len(lines), 8)
        by_product = {
            self.product_a: (12.60, 3.25, 40000.00),
            self.product_b: (18.00, 9.75, 760000.00),
        }
        for product, (ii_rate, ipi_rate, customs_value) in by_product.items():
            group = lines.filtered(
                lambda line, product=product: line.product_id == product
            )
            for line in group:
                self.assertAlmostEqual(line.ii_percent, ii_rate, places=2)
                self.assertAlmostEqual(line.ipi_percent, ipi_rate, places=2)
                self.assertAlmostEqual(
                    line.price_unit * line.quantity, line.ii_base, delta=0.05
                )
            self.assertAlmostEqual(
                sum(line.price_unit * line.quantity for line in group),
                customs_value,
                delta=0.05,
            )
        self.assertAlmostEqual(
            sum(line.price_unit * line.quantity for line in lines),
            800000.00,
            delta=0.05,
        )
        self.assertAlmostEqual(document.amount_price_gross, 800000.00, delta=0.05)

    def test_the_note_closes_on_the_declaration_totals(self):
        wizard = self._wizard()
        self._align_contributions(wizard)

        wizard.action_generate_document()
        document = wizard.document_id

        lines = document.fiscal_line_ids
        self.assertAlmostEqual(document.amount_ii_value, 141840.00, places=2)
        self.assertAlmostEqual(sum(lines.mapped("ii_value")), 141840.00, places=2)
        self.assertAlmostEqual(
            sum(lines.mapped("ii_customhouse_charges")), 150.00, places=2
        )
        self.assertAlmostEqual(
            document.amount_ipi_value, 88901.80, delta=0.01 * len(lines)
        )
        self.assertAlmostEqual(
            document.fiscal_amount_total,
            800000.00
            + 141840.00
            + document.amount_ipi_value
            + document.amount_other_value
            + sum(lines.mapped("icms_value")),
            delta=0.05,
        )

    def test_a_good_without_line_and_a_line_without_good_are_both_named(self):
        self.bill_lines[2].name = "NOT IN THE DECLARATION"

        wizard = self._wizard()

        first = self._addition(wizard, "001")
        self.assertEqual(first.line_ids, self.bill_lines[:2])
        self.assertEqual(first.unmatched, "MERCADORIA 3 DA ADICAO 1, quantity 8.0")
        self.assertEqual(wizard.unclaimed_lines, "NOT IN THE DECLARATION, quantity 8.0")
        self.assertFalse(self._addition(wizard, "002").unmatched)

    def test_an_addition_without_any_line_is_refused_by_number(self):
        for line in self.bill_lines[3:]:
            line.name = "NOT IN THE DECLARATION"
        wizard = self._wizard()
        self.assertFalse(self._addition(wizard, "002").line_ids)

        with self.assertRaisesRegex(UserError, "Addition 002"):
            wizard.action_generate_document()

    def test_the_quantity_breaks_the_tie_between_equal_descriptions(self):
        goods = parse_declaration(FIXTURE.read_bytes())["additions"][0]["items"]
        for item in goods:
            item["description"] = "SAME PART"
        # Bill order 2, 8, 6 against declaration order 6, 2, 8.
        lines = self.bill_lines[:3]
        for line, quantity in zip(lines, (2.0, 8.0, 6.0), strict=True):
            line.write({"name": "SAME PART", "quantity": quantity})
        wizard = self._wizard()

        matched, unmatched = wizard._match_goods(goods, lines)

        self.assertEqual(matched.mapped("quantity"), [6.0, 2.0, 8.0])
        self.assertFalse(unmatched)

    def _align_contributions(self, wizard):
        """Make the declared PIS, COFINS and ICMS the ones the product file computes.

        The amounts of the fixture are made up, and the rate of these taxes
        belongs to the product and to the CFOP, so the check would refuse the
        note. The IPI is left as the file states it: the rate
        of each classification is configured to be the file's own.
        """
        Line = self.env["l10n_br_fiscal.document.line"]
        icms_total = 0.0
        lines_count = len(wizard._bill_lines())
        for addition in wizard.addition_ids:
            totals = {"pis_value": 0.0, "cofins_value": 0.0}
            for bill_line in addition.line_ids:
                share = bill_line.price_subtotal / sum(
                    addition.line_ids.mapped("price_subtotal")
                )
                gross = addition.customs_value * share
                probe = Line.new(
                    dict(
                        wizard._prepare_line_values(bill_line, gross),
                        ii_declared_value=addition.ii_value * share,
                        ii_value=addition.ii_value * share,
                        ii_base=gross,
                        partner_id=wizard.partner_id.id,
                    )
                )
                for fname in totals:
                    totals[fname] += probe[fname]
                rate = probe.icms_percent / 100.0
                icms_total += (
                    (
                        gross
                        + addition.ii_value * share
                        + wizard.customhouse_charges / lines_count
                        + probe.ipi_value
                        + probe.pis_value
                        + probe.cofins_value
                    )
                    / (1 - rate)
                    * rate
                )
            addition.write(totals)
        wizard.icms_value = icms_total
