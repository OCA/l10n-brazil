# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tools import mute_logger

from .common import PAYER, PAYER_2, DdaCommon, make_cnpj

DEBIT_LOGGER = "odoo.addons.l10n_br_dda.models.dda_debit"


class TestUpsert(DdaCommon):
    def test_upsert_is_idempotent_and_dedups_sources(self):
        vals = self.boleto(make_cnpj("814323900001"), 150.0, self.day(5))
        first = self.upsert(vals, source_key="connection:1")
        second = self.upsert(vals, source_key="connection:1")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)
        # The same boleto seen in another connection and in a CNAB file.
        self.upsert(vals, source_key="connection:2")
        self.upsert(vals, source_type="cnab", source_key="cnab:abc")
        self.assertEqual(len(first.source_ids), 3)
        self.assertEqual(
            sorted(first.source_ids.mapped("source_key")),
            ["cnab:abc", "connection:1", "connection:2"],
        )
        count = self.env["l10n_br_dda.debit"].search_count(
            [("digitable_line", "=", vals["digitable_line"])]
        )
        self.assertEqual(count, 1)

    def test_digitable_line_is_normalized(self):
        vals = self.boleto(make_cnpj("717103450001"), 99.0, self.day(5))
        formatted = vals["digitable_line"]
        vals["digitable_line"] = f"{formatted[:5]}.{formatted[5:]}"
        debit = self.upsert(vals)
        self.assertEqual(debit.digitable_line, formatted)

    def test_never_overwrites_known_due_date_with_empty(self):
        vals = self.boleto(make_cnpj("754413400001"), 80.0, self.day(7))
        debit = self.upsert(vals)
        again = dict(vals, date_due="0001-01-01")
        self.upsert(again)
        self.assertEqual(debit.date_due, self.day(7))
        self.upsert(dict(vals, date_due=None, amount=81.0))
        self.assertEqual(debit.date_due, self.day(7))
        self.assertEqual(debit.amount, 81.0)

    def test_routes_company_by_payer_cnpj(self):
        vendor = make_cnpj("841914670001")
        one = self.upsert(self.boleto(vendor, 10.0, self.day(3)))
        two = self.upsert(self.boleto(vendor, 10.0, self.day(3), payer_cnpj=PAYER_2))
        self.assertEqual(one.company_id, self.company)
        self.assertEqual(two.company_id, self.company_2)
        with mute_logger(DEBIT_LOGGER):
            unknown = self.upsert(
                self.boleto(
                    vendor, 10.0, self.day(3), payer_cnpj=make_cnpj("829863969999")
                )
            )
        self.assertFalse(unknown)

    def test_cnpj_display_fields_are_masked(self):
        debit = self.Debit.create(
            {
                "payer_cnpj": PAYER,
                "digitable_line": "3888" + "9" * 43,
                "beneficiary_vat": "12ABC34501DE35",
                "guarantor_vat": "94623756000130",
                "amount": 10.0,
            }
        )
        self.assertEqual(debit.payer_cnpj_display, "82.688.625/0001-52")
        self.assertEqual(debit.beneficiary_vat_display, "12.ABC.345/01DE-35")
        self.assertEqual(debit.guarantor_vat_display, "94.623.756/0001-30")
        # The raw fields stay digits only, for search and filters.
        self.assertEqual(debit.beneficiary_vat, "12ABC34501DE35")
        # A CPF or an empty value is not forced into the CNPJ shape.
        debit.guarantor_vat = False
        debit.beneficiary_vat = "12345678901"
        self.assertFalse(debit.guarantor_vat_display)
        self.assertEqual(debit.beneficiary_vat_display, "12345678901")

    def test_alphanumeric_payer_is_text(self):
        vals = self.boleto(
            "12ABC34501DE35", 10.0, self.day(3), payer_cnpj="99ABC34501DE35"
        )
        with mute_logger(DEBIT_LOGGER):
            self.assertFalse(self.upsert(vals))
        normalized = self.Debit._dda_normalize_vals(
            {"beneficiary_vat": "12.abc.345/01de-35"}
        )
        self.assertEqual(normalized["beneficiary_vat"], "12ABC34501DE35")

    def test_paid_from_source_is_paid_elsewhere_without_posting(self):
        vendor = self.make_vendor("Pago Fora", "753842030001")
        bill = self.make_bill(vendor, 300.0, self.day(4))
        vals = self.boleto(self.cnpj_of(vendor), 300.0, self.day(4))
        debit = self.upsert(vals)
        moves_before = self.env["account.move"].search_count([])
        self.upsert(dict(vals, status="PAGO"))
        self.assertEqual(debit.state, "paid_elsewhere")
        self.assertEqual(self.env["account.move"].search_count([]), moves_before)
        self.assertEqual(bill.payment_state, "not_paid")

    def test_cancelled_warns_linked_bill(self):
        vendor = self.make_vendor("Cancelado", "832534770001")
        bill = self.make_bill(vendor, 310.0, self.day(4))
        vals = self.boleto(self.cnpj_of(vendor), 310.0, self.day(4))
        debit = self.upsert(vals)
        debit.action_link(self.payable_line(bill).ids)
        self.assertEqual(debit.state, "linked")
        before = len(bill.message_ids)
        self.upsert(dict(vals, status="CANCELADO"))
        self.assertEqual(debit.state, "cancelled")
        self.assertGreater(len(bill.message_ids), before)
        # The line is free again for another boleto.
        other = self.upsert(self.boleto(self.cnpj_of(vendor), 310.0, self.day(4)))
        self.assertEqual(other.match_ids.move_line_ids, self.payable_line(bill))

    def test_out_of_order_update_is_ignored(self):
        vals = self.boleto(make_cnpj("742305220001"), 55.0, self.day(9))
        newer = datetime(2026, 10, 20, 12, 0, 0)
        older = datetime(2026, 10, 19, 12, 0, 0)
        debit = self.upsert(dict(vals, updated_at=newer))
        self.upsert(dict(vals, amount=999.0, updated_at=older))
        self.assertEqual(debit.amount, 55.0)

    def test_refused_is_ignored_and_open_again_reopens_cancelled(self):
        vals = self.boleto(make_cnpj("896874190001"), 70.0, self.day(9))
        debit = self.upsert(dict(vals, status="RECUSADO"))
        self.assertEqual(debit.state, "ignored")
        other = self.boleto(make_cnpj("896874190001"), 71.0, self.day(9))
        debit2 = self.upsert(dict(other, status="CANCELADO"))
        self.assertEqual(debit2.state, "cancelled")
        self.upsert(other)
        self.assertIn(debit2.state, ("new", "suggested", "suspect"))
        self.assertTrue(PAYER)
