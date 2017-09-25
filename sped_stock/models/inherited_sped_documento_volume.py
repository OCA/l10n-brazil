# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedDocumentoVolume(models.Model):
    _inherit = 'sped.documento.volume'

    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Transferência de Estoque',
        copy=False,
    )
