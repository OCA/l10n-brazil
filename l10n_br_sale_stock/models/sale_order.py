# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Make Invisible Invoice Button
    sale_create_invoice_policy = fields.Selection(
        related='company_id.sale_create_invoice_policy',
    )
