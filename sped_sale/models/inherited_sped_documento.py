# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido de Venda',
        ondelete='restrict',
        copy=False,
    )
