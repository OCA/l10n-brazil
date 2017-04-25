# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedAliquotaIPI(models.Model):
    _name = b'sped.aliquota.ipi'
    _inherit = 'sped.aliquota.ipi'

    ncm_ids = fields.One2many(
        comodel_name='sped.ncm',
        inverse_name='al_ipi_id',
        string='NCMs'
    )
