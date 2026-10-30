# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import api, fields, models

from ..constants import DEBIT_MODEL
from ..utils import build_digitable_line, format_cnpj, normalize_cnpj

_logger = logging.getLogger(__name__)

# Fictitious vendors: every name and CNPJ is invented.
DEMO_VENDORS = {
    "alfa": ("ALFA EMBALAGENS LTDA", "94623756000130"),
    "beta": ("BETA PAPEIS S.A.", "92455101000175"),
    "gama": ("GAMA LOGISTICA LTDA", "93449834000160"),
    "delta": ("DELTA LOCACOES LTDA", "91428659000107"),
    "epsilon": ("EPSILON INDUSTRIA LTDA", "95564920000149"),
    "zeta": ("ZETA METALURGICA LTDA", "93685439000186"),
    "eta": ("ETA SUPRIMENTOS LTDA", "90889030000193"),
    "teta": ("TETA MANUTENCAO LTDA", "97282349000103"),
    "iota": ("IOTA GRAFICA LTDA", "93493719000192"),
}
# Issuing bank of each demo boleto, by order.
DEMO_BANKS = {
    1: "341",
    2: "001",
    3: "237",
    4: "104",
    5: "104",
    6: "208",
    7: "756",
    8: "001",
    9: "341",
    10: "237",
    11: "104",
    12: "104",
}
DEMO_ASSIGNEE = ("OMEGA SECURITIZADORA DE CREDITOS S.A.", "95916996000196")
DEMO_UNKNOWN = ("SIGMA SERVICOS LTDA", "45000007000141")


class DdaDebitDemo(models.Model):
    _inherit = DEBIT_MODEL

    @api.model
    def _dda_demo_partner(self, name, cnpj):
        partner = self.env["res.partner"].create(
            {
                "name": name,
                "legal_name": name,
                "is_company": True,
                "cnpj_cpf": format_cnpj(cnpj),
                "country_id": self.env.ref("base.br").id,
                "supplier_rank": 1,
            }
        )
        return partner

    @api.model
    def _dda_demo_bill(self, company, journal, partner, amount, due, number):
        bill = (
            self.env["account.move"]
            .with_company(company)
            .create(
                {
                    "move_type": "in_invoice",
                    "company_id": company.id,
                    "journal_id": journal.id,
                    "partner_id": partner.id,
                    "invoice_date": fields.Date.context_today(self),
                    "invoice_date_due": due,
                    "invoice_payment_term_id": False,
                    "ref": number,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Demo purchase %s" % number,
                                "quantity": 1.0,
                                "price_unit": amount,
                            },
                        )
                    ],
                }
            )
        )
        bill.action_post()
        bill.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        ).write({"document_number": number})
        return bill

    @api.model
    def _dda_demo_load(self):
        """Fictitious vendors, vendor bills and boletos for the CNPJ of the main
        company, covering the matching cases."""
        company = self.env.ref("base.main_company")
        journal = self.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", company.id)], limit=1
        )
        if not journal:
            _logger.info("DDA demo skipped: the company has no purchase journal.")
            return False
        payer = normalize_cnpj(company.partner_id.cnpj_cpf)
        if len(payer) != 14:
            _logger.info("DDA demo skipped: the company has no CNPJ.")
            return False
        partner_model = self.env["res.partner"]
        if partner_model.search_count([("cnpj_cpf_stripped", "=", "94623756000130")]):
            return False
        company.dda_create_bill_mode = "draft"
        vendors = {
            key: self._dda_demo_partner(name, cnpj)
            for key, (name, cnpj) in DEMO_VENDORS.items()
        }
        assignee = self._dda_demo_partner(*DEMO_ASSIGNEE)
        vendors["epsilon"].dda_assignee_ids = assignee
        today = fields.Date.context_today(self)

        def day(offset):
            return today + timedelta(days=offset)

        bill = self._dda_demo_bill
        bill(company, journal, vendors["alfa"], 1240.00, day(5), "1001")
        bill(company, journal, vendors["beta"], 3500.00, day(8), "2002")
        bill(company, journal, vendors["gama"], 890.00, day(7), "3003")
        bill(company, journal, vendors["delta"], 2500.00, day(15), "4004/1")
        bill(company, journal, vendors["delta"], 2500.00, day(15), "4004/2")
        bill(company, journal, vendors["epsilon"], 4200.00, day(9), "5005")
        bill(company, journal, vendors["zeta"], 1800.00, day(11), "7007")
        bill(company, journal, vendors["zeta"], 1200.00, day(11), "7008")
        bill(company, journal, vendors["teta"], 1100.00, day(-3), "8008")
        bill(company, journal, vendors["iota"], 680.00, day(7), "9009")

        # The bank API brings no document number, discount, interest or fine.
        def boleto(n, cnpj, name, amount, due):
            return {
                "payer_cnpj": payer,
                "digitable_line": build_digitable_line(
                    DEMO_BANKS[n], amount, due, f"{payer}:{n}"
                ),
                "beneficiary_vat": cnpj,
                "beneficiary_name": name,
                "amount": amount,
                "date_due": due,
                "date_limit": due + timedelta(days=60),
                "external_id": "demo-%s" % n,
            }

        v = DEMO_VENDORS
        vals_list = [
            boleto(1, v["alfa"][1], v["alfa"][0], 1240.00, day(5)),
            boleto(2, v["beta"][1], v["beta"][0], 3587.50, day(8)),
            boleto(3, v["gama"][1], v["gama"][0], 890.00, day(10)),
            boleto(4, v["delta"][1], v["delta"][0], 2500.00, day(15)),
            boleto(5, v["delta"][1], v["delta"][0], 2500.00, day(15)),
            boleto(6, DEMO_ASSIGNEE[1], DEMO_ASSIGNEE[0], 4200.00, day(9)),
            boleto(7, DEMO_UNKNOWN[1], DEMO_UNKNOWN[0], 760.00, day(6)),
            boleto(8, v["zeta"][1], v["zeta"][0], 3000.00, day(11)),
            boleto(9, v["eta"][1], v["eta"][0], 540.00, day(4)),
            boleto(10, v["teta"][1], v["teta"][0], 1100.00, day(-3)),
            boleto(11, v["iota"][1], v["iota"][0], 680.00, day(7)),
            boleto(12, v["iota"][1], v["iota"][0], 680.00, day(7)),
        ]
        self._dda_upsert(vals_list, "manual", "demo")
        return True
