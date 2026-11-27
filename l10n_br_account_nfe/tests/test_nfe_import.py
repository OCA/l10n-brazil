# Copyright 2025 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import re
from datetime import timedelta

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_account_nfe

FIXTURE = os.path.join(
    l10n_br_account_nfe.__path__[0],
    "tests",
    "nfe",
    "35231149647316000169550010000661061151600085-nfe.xml",
)
FIXTURE_DEST = re.compile(rb"(<dest>\s*)<(?:CNPJ|CPF)>\d+</(?:CNPJ|CPF)>")
DUE_ACCOUNT_TYPES = ("asset_receivable", "liability_payable")


class NFeImportTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.user = cls.env["res.users"].create(
            {
                "name": "Because I am accountman!",
                "login": "accountman",
                "password": "accountman",
                "groups_id": [
                    Command.set(cls.env.user.groups_id.ids),
                    Command.link(cls.env.ref("account.group_account_manager").id),
                    Command.link(cls.env.ref("account.group_account_user").id),
                    Command.link(cls.env.ref("l10n_br_fiscal.group_user").id),
                    Command.link(cls.env.ref("l10n_br_nfe.group_manager").id),
                ],
            }
        )
        cls.user.partner_id.email = "accountman@test.com"
        companies = cls.env["res.company"].search([])
        cls.user.write(
            {
                "company_ids": [Command.set(companies.ids)],
                "company_id": cls.company.id,
            }
        )
        cls.env = cls.env(
            user=cls.user,
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=[cls.company.id],
            ),
        )
        cls.operation = cls.env.ref("l10n_br_fiscal.fo_compras")

    def _xml(self, replace=()):
        with open(FIXTURE, "rb") as xml_file:
            content = xml_file.read()
        recipient = self.company.partner_id.cnpj_cpf_stripped
        content = FIXTURE_DEST.sub(rb"\1<CNPJ>%s</CNPJ>" % recipient.encode(), content)
        for old, new in replace:
            content = re.sub(old, new, content, flags=re.S)
        return content

    def _import(self, content):
        documents, errors, _warnings = self.env[
            "l10n_br_fiscal.document"
        ]._edi_import_files([("nfe.xml", content)])
        self.assertFalse(errors)
        return documents

    def _review(self, document):
        """What the user does on the lines: choose a product for each one."""
        document.fiscal_operation_id = self.operation
        for line in document.fiscal_line_ids:
            line._apply_import_depara(
                product=self.env["product.product"].create({"name": line.name}),
                uom=self.env["uom.uom"]._match_by_fiscal_code(line.partner_uom_code),
                fiscal_operation=self.operation,
            )

    def _generate(self, document):
        action = document.action_generate_invoice()
        return self.env["account.move"].browse(action["res_id"])

    def _payables(self, partner):
        return self.env["account.move.line"].search(
            [
                ("partner_id", "=", partner.id),
                ("account_id.account_type", "in", DUE_ACCOUNT_TYPES),
            ]
        )

    def _due_lines(self, move):
        return move.line_ids.filtered(
            lambda line: line.account_id.account_type in DUE_ACCOUNT_TYPES
        ).sorted("date_maturity")

    def test_import_in_nfe(self):
        document = self._import(self._xml())
        self._review(document)
        move = self._generate(document)

        self.assertEqual(move.partner_id.name, "FORNECEDER NFE DEMO LTDA")
        self.assertEqual(move.partner_id.vat, "04.712.500/0001-07")
        self.assertEqual(move.partner_id.l10n_br_ie_code, "078016350838")
        self.assertEqual(
            move.document_type_id, self.env.ref("l10n_br_fiscal.document_55")
        )
        self.assertEqual(move.fiscal_operation_id, self.operation)
        self.assertEqual(move.document_number, "66106")
        self.assertEqual(
            move.document_key, "35231149647316000169550010000661061151600085"
        )

        self.assertAlmostEqual(move.amount_price_gross, 11975.96, places=2)
        self.assertAlmostEqual(move.amount_discount_value, 0, places=2)
        self.assertAlmostEqual(move.amount_untaxed, 11975.96, places=2)
        self.assertAlmostEqual(move.amount_tax, 132.14, places=2)
        self.assertAlmostEqual(move.amount_total, 12108.10, places=2)

        self.assertEqual(len(move.invoice_line_ids), 4)
        line = move.invoice_line_ids[0]
        self.assertEqual(line.quantity, 70.1)
        self.assertAlmostEqual(line.price_unit, 58.0, places=2)
        self.assertAlmostEqual(line.price_subtotal, 4065.80, places=2)
        self.assertEqual(line.nfe40_xPed, "OC00589")
        self.assertEqual(line.icms_tax_id.id, self.ref("l10n_br_fiscal.tax_icms_12"))
        self.assertAlmostEqual(line.icms_value, 487.90, places=2)
        self.assertEqual(line.ipi_tax_id.id, self.ref("l10n_br_fiscal.tax_ipi_3_25"))
        self.assertAlmostEqual(line.ipi_value, 132.14, places=2)
        self.assertAlmostEqual(line.pis_value, 23.26, places=2)
        # the supplier declared CFOP 6101 (interstate sale); the de-para
        # recomputes the one of the company, the declared one is preserved
        doc_line = move.fiscal_document_id.fiscal_line_ids[0]
        self.assertEqual(doc_line.partner_cfop_id.code, "6101")
        self.assertNotEqual(doc_line.cfop_id.code, "6101")

    def test_installments_are_born_with_the_invoice_and_follow_the_duplicates(self):
        document = self._import(self._xml())
        self._review(document)
        self.assertFalse(self._payables(document.partner_id))
        self.assertFalse(document.move_ids)

        move = self._generate(document)

        due_lines = self._due_lines(move)
        self.assertEqual(due_lines, self._payables(document.partner_id))
        self.assertEqual(due_lines.mapped("credit"), [4035.63, 4035.63, 4036.84])
        self.assertEqual(
            [line.date_maturity.isoformat() for line in due_lines],
            ["2026-12-09", "2026-12-24", "2027-01-08"],
        )

    def test_installments_that_do_not_add_up_are_spread_by_their_weight(self):
        xml = self._xml(
            [(rb"<vDup>4035.63</vDup>", b"<vDup>1000.00</vDup>")],
        )
        document = self._import(xml)
        self._review(document)
        self.assertIn("installments add up", document.import_warning)

        due_lines = self._due_lines(self._generate(document))

        self.assertEqual(len(due_lines), 3)
        self.assertAlmostEqual(sum(due_lines.mapped("credit")), 12108.10, places=2)
        # declared 1000.00 + 1000.00 + 4036.84: the weight is kept
        self.assertAlmostEqual(
            due_lines[0].credit / due_lines[2].credit, 1000 / 4036.84, places=2
        )
        self.assertEqual(due_lines[0].credit, due_lines[1].credit)

    def test_import_incomplete_document_is_blocked(self):
        """A document with a line missing its product/uom/qty/price must not
        be importable into an account move (SPED data integrity)."""
        document = self._import(self._xml())
        self._review(document)
        # Break one line to simulate an unmatched product.
        document.fiscal_line_ids[0].product_id = False
        with self.assertRaises(UserError):
            document.action_generate_invoice()
        self.assertFalse(document.move_ids)

    def test_import_without_installments_uses_payment_term(self):
        """An NF-e that declares no duplicata must not lose the due dates
        given by the payment term chosen for the vendor bill."""
        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Two installments",
                "line_ids": [
                    Command.create(
                        {"value": "percent", "value_amount": 50.0, "days": 30}
                    ),
                    Command.create(
                        {"value": "balance", "value_amount": 0.0, "days": 60}
                    ),
                ],
            }
        )
        document = self._import(self._xml([(rb"<cobr>.*?</cobr>", b"")]))
        self._review(document)
        self.assertFalse(document.nfe40_dup)
        move = self._generate(document)
        move.invoice_payment_term_id = payment_term

        due_lines = self._due_lines(move)
        self.assertEqual(
            due_lines.mapped("date_maturity"),
            [
                move.invoice_date + timedelta(days=30),
                move.invoice_date + timedelta(days=60),
            ],
        )
        self.assertAlmostEqual(sum(due_lines.mapped("credit")), 12108.10, places=2)

    def test_upload_to_a_vendor_bill_imports_the_nfe_as_a_fiscal_document(self):
        attachment = self.env["ir.attachment"].create(
            {"name": "nfe.xml", "raw": self._xml()}
        )
        journal = self.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", self.company.id)], limit=1
        )

        action = journal.create_document_from_attachment([attachment.id])

        self.assertEqual(action["res_model"], "l10n_br_fiscal.document")
        document = self.env["l10n_br_fiscal.document"].browse(action["res_id"])
        self.assertEqual(
            document.document_key, "35231149647316000169550010000661061151600085"
        )
        self.assertTrue(document.imported_document)
        self.assertFalse(document.move_ids)
        self.assertFalse(self._payables(document.partner_id))
