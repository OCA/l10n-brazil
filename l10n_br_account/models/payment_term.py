# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FiscalPaymentTerm(models.Model):
    _name = "account.payment.term"
    _inherit = ["account.payment.term", "l10n_br_fiscal.payment.term.abstract"]
