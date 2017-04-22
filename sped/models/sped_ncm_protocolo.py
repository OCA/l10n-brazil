# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedNCM(models.Model):
    _name = b'sped.ncm'
    _inherit = 'sped.ncm'

    protocolo_ids = fields.One2many(
        comodel_name='sped.protocolo.icms.ncm',
        inverse_name='ncm_id',
        string='Protocolos',
    )

    def busca_mva(self, protocolo):
        busca = [
            ('ncm_id', '=', self.id),
            ('protocolo_id', '=', protocolo.id),
        ]

        protocolo_ids = self.protocolo_ids.search(busca)

        if len(protocolo_ids) != 0:
            return protocolo_ids[0]

        return
