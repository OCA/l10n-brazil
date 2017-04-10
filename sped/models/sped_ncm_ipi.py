# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models


class AliquotaIPI(models.Model):
    _name = 'sped.aliquota.ipi'
    _inherit = 'sped.aliquota.ipi'

    ncm_ids = fields.One2many(
        comodel_name='sped.ncm',
        inverse_name='al_ipi_id',
        string=u'NCMs'
    )
