# Copyright 2026 - TODAY Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    DOCUMENT_STATE_CANCEL,
    SITUACAO_EDOC_AUTORIZADA,
)

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
class TestDfeUtilization(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_normal_company_taxes()

    def _vendor_bill(self, number, imported=False, key_body=None):
        move = self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number=number,
            post=True,
        )
        if imported:
            values = {
                "imported_document": True,
                "issuer": DOCUMENT_ISSUER_PARTNER,
                "document_key": _nfe_access_key(key_body),
            }
            # Without l10n_br_fiscal_edi the selection stops at open. When
            # the authorized value exists, use it: that is the source state
            # a posted imported document keeps.
            allowed = {
                key
                for key, _label in move.fiscal_document_id._fields[
                    "state_edoc"
                ]._description_selection(move.env)
            }
            if SITUACAO_EDOC_AUTORIZADA in allowed:
                values["state_edoc"] = SITUACAO_EDOC_AUTORIZADA
            move.write(values)
        return move

    def _inbox(self, move, document_state="1"):
        model = self.env.get("l10n_br_fiscal_dfe.document")
        if model is None:
            return None
        # The inbox is filled by the distribution service, not by the
        # accountant. Fiscal users have no create right on it.
        inbox = model.sudo().create(
            {
                "access_key": move.document_key,
                "company_id": move.company_id.id,
                "fiscal_type": "nfe",
                "document_state": document_state,
            }
        )
        inbox.invalidate_recordset()
        return inbox

    def test_only_a_posted_vendor_bill_counts_as_posted(self):
        draft = self.init_invoice(
            "in_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_compras"),
            fiscal_operation_lines=[
                self.env.ref("l10n_br_fiscal.fo_compras_compras_comercializacao")
            ],
            document_serie="1",
            document_number="91011",
        )
        self.assertFalse(draft.fiscal_document_id.dfe_utilization_from_bills())

        posted = self._vendor_bill("91012")
        self.assertEqual(
            posted.fiscal_document_id.dfe_utilization_from_bills(), "posted"
        )
        posted.button_cancel()
        self.assertFalse(posted.fiscal_document_id.dfe_utilization_from_bills())

    def test_cancelling_an_imported_bill_keeps_the_document_available(self):
        move = self._vendor_bill(
            "91001",
            imported=True,
            key_body="3520015959431500015755001000000091206277716",
        )
        state_before = move.state_edoc
        self.assertNotEqual(state_before, DOCUMENT_STATE_CANCEL)
        inbox = self._inbox(move)
        if inbox is not None:
            self.assertEqual(inbox.fiscal_document_id, move.fiscal_document_id)
            self.assertEqual(inbox.utilization, "posted")

        move.button_cancel()

        self.assertEqual(move.state, "cancel")
        self.assertEqual(move.state_edoc, state_before)
        if inbox is not None:
            inbox.invalidate_recordset()
            self.assertEqual(inbox.utilization, "available")

    def test_a_source_cancelled_document_stays_empty(self):
        move = self._vendor_bill(
            "91002",
            imported=True,
            key_body="3520015959431500015755001000000092206277716",
        )
        state_before = move.state_edoc
        inbox = self._inbox(move, document_state="3")
        if inbox is None:
            self.skipTest("l10n_br_fiscal_dfe is not installed")
        self.assertFalse(inbox.utilization)

        move.button_cancel()

        self.assertEqual(move.state_edoc, state_before)
        inbox.invalidate_recordset()
        self.assertFalse(inbox.utilization)
        inbox.document_state = "2"
        self.assertFalse(inbox.utilization)

    def test_cancelling_a_company_invoice_cancels_the_fiscal_document(self):
        move = self.init_invoice(
            "out_invoice",
            products=[self.product_a],
            document_type=self.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=self.empresa_lc_document_55_serie_1,
            fiscal_operation=self.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[self.env.ref("l10n_br_fiscal.fo_venda_venda")],
            post=True,
        )
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
        self.assertEqual(move.state_edoc, DOCUMENT_STATE_CANCEL)

    def test_cancelling_a_manual_vendor_bill_cancels_the_fiscal_document(self):
        move = self._vendor_bill("91003")
        self.assertFalse(move.imported_document)
        move.button_cancel()
        self.assertEqual(move.state, "cancel")
        self.assertEqual(move.state_edoc, DOCUMENT_STATE_CANCEL)
