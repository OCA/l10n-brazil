# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from odoo import api, fields, models, _


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    purchase_line_id = fields.Many2one(
        string='Linha do pedido',
        comodel_name='purchase.order.line',
    )

    purchase_id = fields.Many2one(
        string='Pedido de compra',
        comodel_name='purchase.order',
        related='purchase_line_id.order_id',
    )
