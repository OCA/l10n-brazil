# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'stock.picking'

    invoice_state = fields.Selection(
        copy=True,
    )
