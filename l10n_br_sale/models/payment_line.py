# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class FiscalPaymentLine(models.Model):
    _inherit = 'l10n_br_fiscal.payment.line'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Invoice',
        related='payment_id.sale_id',
        store=True,
    )
