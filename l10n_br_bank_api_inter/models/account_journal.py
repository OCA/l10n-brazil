# Copyright 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):

    _inherit = "account.journal"

    bank_inter_cert = fields.Binary(string="Bank Inter Certificate")

    bank_inter_key = fields.Binary(string="Bank Inter Key")

    bank_client_id = fields.Char(
        string="Client ID",
        help="Client ID provided by the bank",
    )

    bank_secret_id = fields.Char(
        string="Secret ID",
        help="Secret ID provided by the bank",
    )
