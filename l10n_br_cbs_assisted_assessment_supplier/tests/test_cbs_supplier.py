# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

# NF-e keys accepted by l10n_br_fiscal_edi (model 55 and a valid check digit).
KEY_APPROPRIATED = "35260855444333000100550010000000011123456783"
KEY_DENIED = "35260819131243000197550010000000021123456780"
SUPPLIER_VAT = "55.444.333/0001-00"
SUPPLIER_TAX_ID = "55444333000100"
OTHER_VAT = "19.131.243/0001-97"
OTHER_TAX_ID = "19131243000197"
UNLINKED_TAX_ID = "99888777000166"


class TestCbsSupplier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.period = cls.env["l10n_br_assisted_assessment.period"].create(
            {
                "company_id": cls.company.id,
                "tribute": "cbs",
                "per_apur": "2026-08",
            }
        )
        cls.supplier_model = cls.env["l10n_br_cbs_assisted_assessment.supplier"]
        cls.partner = cls._partner("CBS Credit Supplier", SUPPLIER_VAT)
        cls.other = cls._partner("CBS Other Supplier", OTHER_VAT)
        cls.product = cls.env["product.product"].search([], limit=1)

    @classmethod
    def _partner(cls, name, vat):
        tax_id = "".join(char for char in vat if char.isalnum())
        partner = cls.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", tax_id)], limit=1
        )
        if partner:
            return partner
        return cls.env["res.partner"].create(
            {
                "name": name,
                "is_company": True,
                "country_id": cls.env.ref("base.br").id,
                "vat": vat,
            }
        )

    def _document(self, partner, key, cbs_value=0.0, authorized=False):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "partner_id": partner.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "document_key": key,
                "document_date": "2026-08-10 12:00:00",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
                "imported_document": True,
            }
        )
        if authorized:
            # The assessment reads authorized documents. The EDI state machine
            # does not have to be installed for this board, so the state is
            # stored directly.
            self.env.cr.execute(
                """
                UPDATE l10n_br_fiscal_document
                   SET state_edoc = 'autorizada'
                 WHERE id = %s
                """,
                (document.id,),
            )
            document.invalidate_recordset()
        if cbs_value:
            self.env["l10n_br_fiscal.document.line"].create(
                {
                    "document_id": document.id,
                    "product_id": self.product.id,
                    "cbs_value": cbs_value,
                }
            )
        return document

    def _credit(self, key, appropriated, partner=None, **appropriation):
        document = self._document(partner, key) if partner else False
        detail = {
            "apropriado": appropriated,
            "inapropriavel": appropriation.get("not_appropriable", 0.0),
            "suspenso": appropriation.get("suspended", 0.0),
            "prescrito": appropriation.get("prescribed", 0.0),
        }
        return self.env["l10n_br_assisted_assessment.line"].create(
            {
                "period_id": self.period.id,
                "line_type": "credit",
                "document_key": key,
                "document_id": document.id if document else False,
                "value": appropriated,
                "value_detail": {"apurado": appropriated, "apropriacao": detail},
            }
        )

    def _withholding(self, vat, principal, key=False, number="12345678901234561"):
        payment = self.env["l10n_br_cbs_assisted_assessment.payment"].create(
            {
                "company_id": self.company.id,
                "service": "withholdings",
                "collection_date": "2026-08-15",
                "darf_number": number,
                "payment_type": "1",
            }
        )
        return self.env["l10n_br_cbs_assisted_assessment.payment.line"].create(
            {
                "payment_id": payment.id,
                "sequence": 1,
                "period_id": self.period.id,
                "counterparty_vat": vat,
                "document_key": key,
                "amount_principal": principal,
                "amount_total": principal,
            }
        )

    def _rows(self):
        self.supplier_model._refresh(self.period)
        return self.supplier_model.search([("period_id", "=", self.period.id)])

    def test_appropriated_credit_links_the_supplier(self):
        self.partner.tax_framework = "1"
        self._credit(KEY_APPROPRIATED, 12.0, partner=self.partner)
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.partner_id, self.partner)
        self.assertEqual(row.tax_id, SUPPLIER_TAX_ID)
        self.assertEqual(row.tax_framework, "1")
        self.assertEqual(row.credit_appropriated, 12.0)
        self.assertEqual(row.credit_status, "credits")
        self.assertEqual(row.collection_status, "unknown")

    def test_non_appropriable_and_prescribed_do_not_grant_credit(self):
        self._credit(
            KEY_APPROPRIATED,
            0.0,
            partner=self.partner,
            not_appropriable=4.0,
            prescribed=1.5,
        )
        row = self._rows()
        self.assertEqual(row.credit_not_appropriable, 5.5)
        self.assertEqual(row.credit_appropriated, 0.0)
        self.assertEqual(row.credit_status, "no_credit")

    def test_appropriated_and_non_appropriable_are_partial(self):
        self._credit(
            KEY_APPROPRIATED,
            12.0,
            partner=self.partner,
            not_appropriable=3.0,
        )
        row = self._rows()
        self.assertEqual(row.credit_status, "partial")
        self.assertEqual(row.credit_appropriated, 12.0)
        self.assertEqual(row.credit_not_appropriable, 3.0)

    def test_suspended_credit_has_no_credit_position(self):
        self._credit(KEY_APPROPRIATED, 0.0, partner=self.partner, suspended=3.0)
        row = self._rows()
        self.assertEqual(row.credit_suspended, 3.0)
        self.assertEqual(row.credit_status, "unknown")

    def test_denied_divergence_is_credit_not_granted(self):
        document = self._document(self.other, KEY_DENIED)
        self.env["l10n_br_assisted_assessment.divergence"].create(
            {
                "period_id": self.period.id,
                "divergence_type": "credit_denied",
                "line_type": "credit",
                "document_key": KEY_DENIED,
                "document_id": document.id,
                "fisco_value": 0.0,
                "local_value": 90.0,
            }
        )
        row = self._rows()
        self.assertEqual(row.partner_id, self.other)
        self.assertEqual(row.tax_id, OTHER_TAX_ID)
        self.assertEqual(row.credit_denied, 90.0)
        self.assertEqual(row.credit_status, "no_credit")

    def test_withholding_without_a_partner_is_rad_we_pay(self):
        self._withholding(UNLINKED_TAX_ID, 15.0)
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertFalse(row.partner_id)
        self.assertEqual(row.tax_id, UNLINKED_TAX_ID)
        self.assertEqual(row.rad_paid, 15.0)
        self.assertEqual(row.collection_status, "we_pay")
        self.assertEqual(row.credit_status, "unknown")

    def test_inbound_without_rad_means_the_supplier_collects(self):
        self._document(self.partner, KEY_APPROPRIATED, cbs_value=40.0, authorized=True)
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.partner_id, self.partner)
        self.assertEqual(row.inbound_cbs, 40.0)
        self.assertEqual(row.rad_paid, 0.0)
        self.assertEqual(row.collection_status, "collects")

    def test_payment_rad_is_not_an_acquirer_withholding(self):
        payment = self.env["l10n_br_cbs_assisted_assessment.payment"].create(
            {
                "company_id": self.company.id,
                "service": "payments",
                "collection_date": "2026-08-15",
                "darf_number": "12345678901234562",
                "payment_type": "1",
            }
        )
        self.env["l10n_br_cbs_assisted_assessment.payment.line"].create(
            {
                "payment_id": payment.id,
                "sequence": 1,
                "period_id": self.period.id,
                "counterparty_vat": SUPPLIER_TAX_ID,
                "amount_principal": 80.0,
                "amount_total": 80.0,
            }
        )
        self.assertFalse(self._rows())

    def test_credit_and_rad_stay_on_the_same_supplier(self):
        self._credit(KEY_APPROPRIATED, 12.0, partner=self.partner)
        self._withholding(SUPPLIER_TAX_ID, 15.0, key=KEY_APPROPRIATED)
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.partner_id, self.partner)
        self.assertEqual(row.credit_appropriated, 12.0)
        self.assertEqual(row.credit_status, "credits")
        self.assertEqual(row.rad_paid, 15.0)
        self.assertEqual(row.collection_status, "we_pay")

    def test_rows_are_rebuilt_and_not_editable(self):
        self._credit(KEY_APPROPRIATED, 12.0, partner=self.partner)
        first = self._rows()
        second = self._rows()
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first, second)
        user = self.env.ref("base.user_admin")
        with self.assertRaises(UserError):
            self.supplier_model.with_user(user).create(
                {
                    "period_id": self.period.id,
                    "supplier_key": "manual",
                    "credit_status": "unknown",
                    "collection_status": "unknown",
                }
            )

    def test_period_button_opens_that_period(self):
        self._credit(KEY_APPROPRIATED, 12.0, partner=self.partner)
        action = self.period.action_open_cbs_suppliers()
        self.assertEqual(action["res_model"], self.supplier_model._name)
        self.assertEqual(action["domain"], [("period_id", "=", self.period.id)])
        self.assertEqual(
            self.supplier_model.search_count([("period_id", "=", self.period.id)]),
            1,
        )
        self.assertEqual(self.period.cbs_supplier_count, 1)

    def test_menu_opens_without_write_access(self):
        self._credit(KEY_APPROPRIATED, 12.0, partner=self.partner)
        user = self.env.ref("base.user_admin")
        action = self.env.ref(
            "l10n_br_cbs_assisted_assessment_supplier.action_cbs_supplier_open"
        )
        result = action.with_user(user).run()
        self.assertEqual(result["res_model"], self.supplier_model._name)
        self.assertEqual(
            self.supplier_model.search_count([("period_id", "=", self.period.id)]),
            1,
        )
