# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NCM(models.Model):
    _inherit = 'sped.ncm'
    _name = 'sped.ncm'

    protocolo_ids = fields.One2many('sped.protocolo.icms.ncm', 'ncm_id', 'Protocolos')

    def busca_mva(self, protocolo):
        busca = [
            ('ncm_id', '=', self.id),
            ('protocolo_id', '=', protocolo.id),
        ]

        protocolo_ids = self.protocolo_ids.search(busca)

        if len(protocolo_ids) != 0:
            return protocolo_ids[0]

        return
