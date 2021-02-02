# Copyright (C) 2021 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    sale_create_invoice_policy = fields.Selection(
        selection=[
            ('sale_order', 'Sale Order'),
            ('stock_picking', 'Stock Picking')
        ],
        string='Sale Create Invoice Policy',
        help='Define if Invoice should be create'
             ' from Sale Order or Stock Picking.',
        default='stock_picking'
    )
