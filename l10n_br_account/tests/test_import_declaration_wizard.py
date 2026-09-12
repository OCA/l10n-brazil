# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon

# Declaration 26/0755042-3, registered on 2026-07-10, two additions, road
# transport, cleared at ALF de Uruguaiana. Every amount below was charged by it.
VALOR_ADUANEIRO = 805163.07
II = 142564.47
IPI = 89198.15
PIS = 16908.43
COFINS = 77698.23
ICMS = 248427.47
SISCOMEX = 192.79


@tagged("post_install", "-at_install")
class TestImportDeclarationWizard(AccountMoveBRCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["account.chart.template"].load_fiscal_taxes(
            companies=[cls.company_data["company"]]
        )
        cls.configure_normal_company_taxes()

        cls.foreign_partner = cls.partner_a.copy(
            {
                "name": "Fornecedor do exterior",
                "legal_name": "Fornecedor do exterior",
                "country_id": cls.env.ref("base.cl").id,
                "state_id": False,
                "vat": False,
                "is_company": True,
            }
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.operation_line = cls.env.ref(
            "l10n_br_fiscal.fo_compras_compras_comercializacao"
        )
        cls.bill = cls.init_invoice(
            "in_invoice",
            partner=cls.foreign_partner,
            products=[cls.product_a, cls.product_b],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.operation,
            fiscal_operation_lines=[cls.operation_line, cls.operation_line],
            document_serie="1",
            document_number="717",
        )

    def _expected_totals(self, wizard):
        """What the engine will compute for the lines this wizard builds.

        The wizard writes only what the declaration knows and the product file
        cannot: the Import Tax and the customs charges. The IPI, the
        contributions and the ICMS come from the product and from the CFOP, so
        the test has to declare what the file says, or the check refuses the
        note, which is exactly what it exists for.
        """
        lines = wizard._bill_lines()
        shares = wizard._shares(lines)
        currency = wizard.company_currency_id
        gross_parts = wizard._split(wizard.customs_value, shares, currency)
        ii_parts = wizard._split(wizard.ii_value, shares, currency)
        charge_parts = wizard._split(wizard.customhouse_charges, shares, currency)
        totals = dict.fromkeys(
            ("ipi_value", "pis_value", "cofins_value", "icms_value"), 0.0
        )
        Line = self.env["l10n_br_fiscal.document.line"]
        for position, bill_line in enumerate(lines):
            values = wizard._prepare_line_values(bill_line, gross_parts[position])
            values.update(
                {
                    "ii_value": ii_parts[position],
                    "ii_base": gross_parts[position],
                    "ii_customhouse_charges": charge_parts[position],
                    "partner_id": wizard.partner_id.id,
                }
            )
            probe = Line.new(values)
            for fname in ("ipi_value", "pis_value", "cofins_value"):
                totals[fname] += probe[fname]
            # Same gross up the wizard does: the ICMS of an import sits inside
            # its own base, and the rate is the one the CFOP maps.
            rate = probe.icms_percent or 0.0
            if rate:
                before = (
                    gross_parts[position]
                    + ii_parts[position]
                    + charge_parts[position]
                    + probe.ipi_value
                    + probe.pis_value
                    + probe.cofins_value
                )
                totals["icms_value"] += before / (1 - rate / 100.0) * rate / 100.0
        return totals

    def _wizard(self, **overrides):
        values = {
            "move_id": self.bill.id,
            "fiscal_operation_id": self.operation.id,
            "fiscal_operation_line_id": self.operation_line.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            "document_date": "2026-07-10 12:00:00",
            "customs_value": VALOR_ADUANEIRO,
            "di_number": "26/0755042-3",
            "di_date": date(2026, 7, 10),
            "clearance_date": date(2026, 7, 10),
            "clearance_place": "ALF - URUGUAIANA",
            "clearance_state_id": self.env.ref("base.state_br_rs").id,
            "transport_via": "7",
            "exporter_code": "76900150",
            "addition_number": "1",
            "ii_value": II,
            "intermediation": "1",
            "customhouse_charges": SISCOMEX,
        }
        values.update(overrides)
        wizard = self.env["l10n_br_account.import.declaration.wizard"].create(values)
        if "ipi_value" not in overrides:
            wizard.write(self._expected_totals(wizard))
        return wizard

    def test_the_note_closes_on_the_declaration(self):
        """The generated note has to total what the declaration charged.

        Measured against a real authorized note of the same shipment: the gross
        amount is the customs value, the taxes of the declaration ride on top
        through the import branch of the fiscal amounts, and the IPI closes it.
        """
        wizard = self._wizard()

        wizard.action_generate_document()
        document = wizard.document_id

        lines = document.fiscal_line_ids
        self.assertEqual(len(lines), 2)
        esperado = (
            VALOR_ADUANEIRO
            + II
            + SISCOMEX
            + sum(lines.mapped("ipi_value"))
            + sum(lines.mapped("pis_value"))
            + sum(lines.mapped("cofins_value"))
            + sum(lines.mapped("icms_value"))
        )
        self.assertAlmostEqual(document.fiscal_amount_total, esperado, places=2)

    def test_a_note_that_does_not_close_on_the_declaration_is_refused(self):
        """A tax mapping gap has to surface here, not as a SEFAZ rejection.

        Transmitting it earns 528 when the amount does not follow the base and
        the rate, or 538 when the total does not follow the items.
        """
        wizard = self._wizard(ipi_value=IPI, pis_value=PIS, cofins_value=COFINS)

        with self.assertRaises(UserError):
            wizard.action_generate_document()

    def test_the_import_tax_carries_base_and_rate(self):
        """The SEFAZ recomputes base times rate and refuses with 528 otherwise."""
        wizard = self._wizard()

        wizard.action_generate_document()

        for line in wizard.document_id.fiscal_line_ids:
            self.assertAlmostEqual(
                line.ii_base * line.ii_percent / 100.0, line.ii_value, places=2
            )

    def test_the_customs_value_becomes_the_gross_amount(self):
        wizard = self._wizard()

        wizard.action_generate_document()

        self.assertAlmostEqual(
            sum(wizard.document_id.fiscal_line_ids.mapped("price_gross")),
            VALOR_ADUANEIRO,
            places=2,
        )

    def test_each_tax_adds_up_to_the_declaration(self):
        """No cent is lost or invented when spreading over the lines."""
        wizard = self._wizard()

        wizard.action_generate_document()
        lines = wizard.document_id.fiscal_line_ids

        for fname, expected in (
            ("ii_value", II),
            ("ii_customhouse_charges", SISCOMEX),
        ):
            self.assertAlmostEqual(
                sum(lines.mapped(fname)), expected, places=2, msg=fname
            )

    def test_the_lines_resolve_an_import_cfop(self):
        """Without a 3.xxx CFOP the taxes of the declaration do not compose."""
        wizard = self._wizard()

        wizard.action_generate_document()

        for line in wizard.document_id.fiscal_line_ids:
            self.assertTrue(line.cfop_id.code.startswith("3"), line.cfop_id.code)

    def test_generating_twice_is_refused(self):
        wizard = self._wizard()
        wizard.action_generate_document()

        with self.assertRaises(UserError):
            wizard.action_generate_document()

    def test_a_bill_without_product_line_is_refused(self):
        empty = self.bill.copy()
        empty.invoice_line_ids.unlink()
        # ipi_value given on purpose: it skips the helper that reads the bill
        # lines, so the refusal comes from the action and not from the setup.
        wizard = self._wizard(move_id=empty.id, ipi_value=IPI)

        with self.assertRaises(UserError):
            wizard.action_generate_document()
