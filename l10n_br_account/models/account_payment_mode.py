# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentMode(models.Model):
    _name = 'account.payment.mode'
    _inherit = ['account.payment.mode', 'l10n_br_fiscal.payment.term.abstract']
