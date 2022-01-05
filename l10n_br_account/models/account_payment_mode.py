# -*- coding: utf-8 -*-

from odoo import models, fields, _


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    fiscal_type = fields.Many2one(
        comodel_name="l10n_br_fiscal.payment",
        string="Tipo de Pagamento",
    )
