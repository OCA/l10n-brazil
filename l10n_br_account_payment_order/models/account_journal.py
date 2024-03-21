# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    bank_code_bc = fields.Char(related="bank_id.code_bc")

    inbound_payment_method_ids = fields.Many2many(
        "account.payment.method",
        "account_journal_inbound_payment_method_rel",
        "journal_id",
        "payment_method_id",
        string="Inbound Payment Methods",
        domain=[("payment_type", "=", "inbound")],
        help="Payment methods that can be used for incoming payments",
    )
