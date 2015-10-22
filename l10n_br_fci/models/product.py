# -*- encoding: utf-8 -*-

from openerp import models, fields


class product_fci(models.Model):
    """
    Generate Entries by Statement from Invoices
    """
    _inherit = "product.template"
    _description = "Entries by product template"

    lines_ids = fields.Many2many('product_fci.from.product.template.lines','line_id', 'product_line_rel')