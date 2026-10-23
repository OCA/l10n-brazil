# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


def _nfe_access_key(body):
    """43-digit NF-e key body plus the mod-11 check digit."""
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    total = 0
    for index, digit in enumerate(reversed(body)):
        total += int(digit) * weights[index % 8]
    rest = total % 11
    check = 0 if rest < 2 else 11 - rest
    return body + str(check)


@tagged("post_install", "-at_install")
class TestImportExistingBill(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document_type_55 = cls.env.ref("l10n_br_fiscal.document_55")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        if "l10n_latam.document.type" in cls.env:
            cls._mirror_latam_document_type(cls.document_type_55)
        cls.env.user.groups_id |= cls.env.ref("account.group_account_invoice")
        cls.company = cls.company_data["company"]

    @classmethod
    def _mirror_latam_document_type(cls, document_type):
        fiscal_country = cls.company_data["company"].account_fiscal_country_id
        domain = [
            ("code", "=", document_type.code),
            ("country_id", "=", fiscal_country.id),
        ]
        if cls.env["l10n_latam.document.type"].search_count(domain):
            return
        cls.env["l10n_latam.document.type"].create(
            {
                "name": document_type.name,
                "code": document_type.code,
                "country_id": fiscal_country.id,
                "internal_type": "invoice",
                "doc_code_prefix": "NFe",
            }
        )

    def _key(self, serial):
        body = f"35231149647316000169550010000661061{serial:08d}"
        self.assertEqual(len(body), 43)
        return _nfe_access_key(body)

    def _vendor_bill(self, number, serie="1", products=None, key=False):
        products = products or [self.product_a]
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "document_type_id": self.document_type_55.id,
                "document_serie": serie,
                "document_number": number,
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "partner",
                "partner_id": self.partner_a.id,
                "fiscal_operation_type": "in",
            }
        )
        for product in products:
            self.env["l10n_br_fiscal.document.line"].create(
                self._fiscal_line_vals(document, product)
            )
        move_form = self.env["account.move"].import_fiscal_document(
            document, move_type="in_invoice"
        )
        bill = self.env["account.move"].browse(move_form.id)
        if key:
            bill.fiscal_document_id.document_key = key
        return bill

    def _fiscal_line_vals(self, document, product, quantity=1.0, price=10.0):
        return {
            "document_id": document.id,
            "name": product.display_name,
            "product_id": product.id,
            "quantity": quantity,
            "price_unit": price,
            "fiscal_operation_type": "in",
            "fiscal_operation_id": self.fiscal_operation.id,
            "fiscal_operation_line_id": self.fiscal_operation_line.id,
        }

    def _line_specs(self, bill, price_delta=0.0):
        specs = []
        for line in bill._importable_invoice_lines():
            specs.append(
                {
                    "product": line.product_id,
                    "quantity": line.quantity,
                    "price": line.price_unit + price_delta,
                }
            )
        return specs

    def _wizard(self, bill, number, serie, key, target=True, create_new=False):
        values = {
            "company_id": bill.company_id.id,
            "partner_id": bill.partner_id.id,
            "issuer_partner_id": bill.partner_id.id,
            "document_type_id": bill.document_type_id.id,
            "document_number": number,
            "document_serie": serie,
            "document_key": key,
            "fiscal_operation_id": self.fiscal_operation.id,
            "create_new_move": create_new,
        }
        if target:
            values["target_move_id"] = bill.id
        return self.env["l10n_br_fiscal.document.import.wizard"].create(values)

    def _create_official(self, wizard, specs, icms_value=0.0):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": wizard.company_id.id,
                "fiscal_operation_id": self.fiscal_operation.id,
                "document_type_id": wizard.document_type_id.id,
                "document_serie": wizard.document_serie,
                "document_number": wizard.document_number,
                "document_date": fields.Date.from_string("2026-08-17"),
                "issuer": "partner",
                "partner_id": wizard.partner_id.id,
                "fiscal_operation_type": "in",
                "document_key": (wizard.document_key or "").replace(" ", ""),
                "imported_document": True,
            }
        )
        for spec in specs:
            line = self.env["l10n_br_fiscal.document.line"].create(
                self._fiscal_line_vals(
                    document,
                    spec["product"],
                    quantity=spec["quantity"],
                    price=spec["price"],
                )
            )
            line.price_unit = spec["price"]
            line.quantity = spec["quantity"]
            if icms_value:
                line.icms_value = icms_value
        return None, document

    def _apply(self, wizard, specs, icms_value=0.0):
        def _create_edoc_from_file(self_wizard):
            return self._create_official(self_wizard, specs, icms_value=icms_value)

        with mock.patch.object(
            type(wizard), "_create_edoc_from_file", _create_edoc_from_file
        ):
            return wizard.action_import_and_open_move()

    def test_same_number_completes_the_draft_bill(self):
        bill = self._vendor_bill(number="00810", serie="001")
        specs = self._line_specs(bill)
        key = self._key(1)
        wizard = self._wizard(bill, number="810", serie="1", key=key)
        self.assertTrue(wizard._is_strong_move_match(bill))
        action = self._apply(wizard, specs, icms_value=12.34)
        self.assertEqual(action["res_id"], bill.id)
        self.assertEqual(bill.document_key, key)
        self.assertEqual(bill.document_number, "810")
        self.assertTrue(bill.imported_document)
        product_lines = bill._importable_invoice_lines()
        self.assertEqual(len(product_lines), 1)
        self.assertEqual(
            product_lines.fiscal_document_line_id.document_id,
            bill.fiscal_document_id,
        )
        self.assertAlmostEqual(product_lines.icms_value, 12.34, places=2)
        again = self._wizard(bill, number="810", serie="1", key=key, target=False)
        second = again.action_import_and_open_move()
        self.assertEqual(second["res_id"], bill.id)
        self.assertEqual(
            self.env["account.move"].search_count(
                [
                    ("id", "=", bill.id),
                    ("move_type", "=", "in_invoice"),
                    ("partner_id", "=", self.partner_a.id),
                    ("document_number", "=", "810"),
                ]
            ),
            1,
        )

    def test_pasted_key_is_replaced_by_the_xml(self):
        key = self._key(2)
        bill = self._vendor_bill(number="811", serie="1", key=key)
        self.assertFalse(bill.imported_document)
        specs = self._line_specs(bill)
        wizard = self._wizard(bill, number="811", serie="1", key=key)
        self._apply(wizard, specs)
        self.assertTrue(bill.imported_document)
        self.assertEqual(bill.document_key, key)
        self.assertEqual(len(bill._importable_invoice_lines()), 1)

    def test_two_candidates_require_a_choice(self):
        first = self._vendor_bill(number="821", serie="1")
        second = self._vendor_bill(number="822", serie="1")
        wizard = self._wizard(
            first, number="999", serie="1", key=self._key(3), target=False
        )
        with self.assertRaises(UserError):
            wizard.action_import_and_open_move()
        self.assertEqual(first.document_number, "821")
        self.assertEqual(second.document_number, "822")
        self.assertFalse(first.imported_document)
        self.assertFalse(second.imported_document)

    def test_posted_bill_blocks_the_import(self):
        bill = self._vendor_bill(number="830", serie="1")
        self.env.cr.execute(
            "UPDATE account_move SET state = 'posted' WHERE id = %s", (bill.id,)
        )
        bill.invalidate_recordset()
        wizard = self._wizard(bill, number="830", serie="1", key=self._key(4))
        with self.assertRaises(UserError):
            wizard.action_import_and_open_move()
        self.assertFalse(bill.imported_document)

    def test_divergence_without_confirmation_keeps_the_shell(self):
        bill = self._vendor_bill(number="840", serie="1")
        number = bill.document_number
        specs = self._line_specs(bill, price_delta=5.0)
        wizard = self._wizard(bill, number="840", serie="1", key=self._key(5))
        with self.assertRaises(UserError):
            self._apply(wizard, specs)
        bill.invalidate_recordset()
        self.assertEqual(bill.document_number, number)
        self.assertFalse(bill.document_key)
        self.assertEqual(len(bill._importable_invoice_lines()), 1)
        wizard.confirm_divergence = True
        self._apply(wizard, specs)
        self.assertEqual(bill.document_key, self._key(5))
        self.assertTrue(bill.imported_document)

    def test_ambiguous_lines_are_not_paired_automatically(self):
        bill = self._vendor_bill(
            number="841",
            serie="1",
            products=[self.product_a, self.product_a],
        )
        original_ids = set(bill._importable_invoice_lines().fiscal_document_line_id.ids)
        self.assertEqual(len(original_ids), 2)
        specs = self._line_specs(bill)
        wizard = self._wizard(bill, number="841", serie="1", key=self._key(6))
        self._apply(wizard, specs)
        product_lines = bill._importable_invoice_lines()
        self.assertEqual(len(product_lines), 2)
        self.assertEqual(set(product_lines.fiscal_document_line_id.ids), original_ids)

    def test_shell_identity_is_restored_when_the_xml_fails(self):
        key = self._key(7)
        bill = self._vendor_bill(number="850", serie="1", key=key)
        wizard = self._wizard(bill, number="850", serie="1", key=key)

        def _boom(self_wizard):
            raise UserError(_("XML rejected"))

        with mock.patch.object(type(wizard), "_create_edoc_from_file", _boom):
            with self.assertRaises(UserError):
                wizard.action_import_and_open_move()
        bill.invalidate_recordset()
        self.assertEqual(bill.document_key, key)
        self.assertEqual(bill.document_number, "850")
        self.assertFalse(bill.imported_document)

    def test_other_company_document_is_not_reused(self):
        other = self._create_company(
            name="Import company B",
            country_id=self.env.ref("base.br").id,
            currency_id=self.env.ref("base.BRL").id,
            vat="32.606.743/0001-04",
        )
        self.env["account.chart.template"].load_fiscal_taxes(companies=[other])
        key = self._key(8)
        other_document = (
            self.env["l10n_br_fiscal.document"]
            .with_company(other)
            .create(
                {
                    "company_id": other.id,
                    "fiscal_operation_id": self.fiscal_operation.id,
                    "document_type_id": self.document_type_55.id,
                    "document_serie": "1",
                    "document_number": "860",
                    "document_date": fields.Date.from_string("2026-08-17"),
                    "issuer": "partner",
                    "partner_id": self.partner_a.id,
                    "fiscal_operation_type": "in",
                    "document_key": key,
                    "imported_document": True,
                }
            )
        )
        self.env["l10n_br_fiscal.document.line"].create(
            self._fiscal_line_vals(other_document, self.product_a)
        )
        other_bill_form = (
            self.env["account.move"]
            .with_company(other)
            .import_fiscal_document(other_document, move_type="in_invoice")
        )
        other_bill = self.env["account.move"].browse(other_bill_form.id)
        bill = self._vendor_bill(number="860", serie="1")
        wizard = self._wizard(bill, number="860", serie="1", key=key)
        wizard._prepare_import_candidates()
        self.assertNotIn(other_bill, wizard.candidate_move_ids)
        self.assertIn(bill, wizard.candidate_move_ids)
        found = self.env["l10n_br_fiscal.document"].search(
            [
                ("document_key", "=", key),
                ("company_id", "=", self.company.id),
                ("imported_document", "=", True),
            ]
        )
        self.assertFalse(found)
        self._apply(wizard, self._line_specs(bill))
        self.assertEqual(bill.company_id, self.company)
        self.assertNotEqual(bill.fiscal_document_id, other_document)
        self.assertEqual(bill.fiscal_document_id.company_id, self.company)
        self.assertEqual(other_bill.fiscal_document_id, other_document)

    def test_button_import_does_not_append_imported_lines(self):
        bill = self._vendor_bill(number="870", serie="1")
        specs = self._line_specs(bill)
        official_binding = self._create_official(
            self._wizard(bill, number="871", serie="1", key=self._key(9), target=False),
            specs,
        )
        official = official_binding[1]
        bill.write({"fiscal_document_id": official.id})
        self.assertTrue(bill.imported_document)
        self.assertFalse(bill._fiscal_lines_already_applied())
        bill.button_import_fiscal_document()
        product_lines = bill._importable_invoice_lines()
        self.assertEqual(len(product_lines), 1)
        self.assertEqual(
            product_lines.fiscal_document_line_id, official.fiscal_line_ids
        )
        with self.assertRaises(UserError):
            bill.button_import_fiscal_document()

    def test_new_bill_is_refused_when_the_shell_already_has_the_key(self):
        key = self._key(10)
        bill = self._vendor_bill(number="880", serie="1", key=key)
        wizard = self._wizard(
            bill, number="880", serie="1", key=key, target=False, create_new=True
        )
        with self.assertRaises(UserError):
            wizard.action_import_and_open_move()
        self.assertFalse(bill.imported_document)
        self.assertEqual(bill.document_key, key)
