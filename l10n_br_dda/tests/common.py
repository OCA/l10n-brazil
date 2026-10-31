# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from itertools import count

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_br_dda.utils import normalize_cnpj

PAYER = "82688625000152"
PAYER_2 = "98585666000153"
_COUNTER = count(1)


def make_cnpj(base12):
    """Valid CNPJ from the 12 first digits (tests only)."""
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(c) * w for c, w in zip(base12, weights, strict=True))
    d1 = (11 - total % 11) % 11
    d1 = 0 if d1 > 9 else d1
    base13 = base12 + str(d1)
    total = sum(int(c) * w for c, w in zip(base13, [6] + weights, strict=True))
    d2 = (11 - total % 11) % 11
    d2 = 0 if d2 > 9 else d2
    return base13 + str(d2)


@tagged("post_install", "-at_install")
class DdaCommon(AccountTestInvoicingCommon):
    chart_template = "br_oca_generic"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, lang="en_US")
        )
        cls.company_data_2 = cls.setup_other_company()
        cls.company = cls.company_data["company"]
        cls.company.partner_id.vat = PAYER
        cls.company_2 = cls.company_data_2["company"]
        cls.company_2.partner_id.vat = PAYER_2
        cls.env.user.company_ids |= cls.company | cls.company_2
        cls.env.user.groups_id |= cls.env.ref("l10n_br_dda.group_dda_manager")
        cls.Debit = cls.env["l10n_br_dda.debit"].with_company(cls.company)
        cls.today = fields.Date.context_today(cls.Debit)

    # -- fixtures --------------------------------------------------------
    @classmethod
    def day(cls, offset):
        return cls.today + timedelta(days=offset)

    @classmethod
    def make_vendor(cls, name, base12, **extra):
        cnpj = make_cnpj(base12)
        vals = {
            "name": name,
            "legal_name": name,
            "is_company": True,
            "vat": cnpj,
            "country_id": cls.env.ref("base.br").id,
        }
        vals.update(extra)
        partner = cls.env["res.partner"].create(vals)
        return partner

    @staticmethod
    def cnpj_of(partner):
        return normalize_cnpj(partner.vat)

    @classmethod
    def make_bill(cls, partner, amount, due, number=None, company=None, post=True):
        company = company or cls.company
        data = cls.company_data if company == cls.company else cls.company_data_2
        bill = (
            cls.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "in_invoice",
                    "company_id": company.id,
                    "journal_id": data["default_journal_purchase"].id,
                    "partner_id": partner.id,
                    "invoice_date": cls.today,
                    "invoice_date_due": due,
                    "invoice_payment_term_id": False,
                    "ref": number,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "line",
                                "quantity": 1.0,
                                "price_unit": amount,
                                "account_id": data["default_account_expense"].id,
                            },
                        )
                    ],
                }
            )
        )
        if post:
            bill.action_post()
            if number:
                bill.line_ids.filtered(
                    lambda line: line.account_id.account_type == "liability_payable"
                ).write({"document_number": number})
        return bill

    @classmethod
    def payable_line(cls, bill):
        return bill.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )

    @classmethod
    def boleto(cls, vendor_cnpj, amount, due, **extra):
        n = next(_COUNTER)
        vals = {
            "payer_cnpj": PAYER,
            "digitable_line": f"3888{n:043d}",
            "beneficiary_vat": vendor_cnpj,
            "beneficiary_name": f"Vendor {vendor_cnpj}",
            "amount": amount,
            "date_due": due,
            "external_id": f"ext-{n}",
        }
        vals.update(extra)
        return vals

    @classmethod
    def upsert(cls, *vals, source_type="api", source_key="connection:1"):
        return cls.Debit._dda_upsert(list(vals), source_type, source_key)
