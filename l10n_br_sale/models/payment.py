# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalPayment(models.Model):
    _inherit = "l10n_br_fiscal.payment"

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale',
        ondelete='cascade',
    )
