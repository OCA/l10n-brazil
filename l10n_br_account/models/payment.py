# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FiscalPayment(models.Model):
    _inherit = "l10n_br_fiscal.payment"

    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
    )

