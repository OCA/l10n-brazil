# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FiscalPayment(models.Model):
    _name = 'l10n_br_fiscal.payment.mode'
    _inherit = ['l10n_br_fiscal.payment.mode', 'account.payment.mode']
    _table = 'account_payment_mode'
