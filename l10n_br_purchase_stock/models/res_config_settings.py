# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_create_invoice_policy = fields.Selection(
        selection=[
            ('purchase_order', _('Purchase Order')),
            ('stock_picking', _('Stock Picking'))],
        string='Purchase Create Invoice Policy',
        related='company_id.purchase_create_invoice_policy',
        readonly=False,
    )
