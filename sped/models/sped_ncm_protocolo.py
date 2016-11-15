# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NCM(models.Model):
    _inherit = 'sped.ncm'
    _name = 'sped.ncm'

    protocolo_ids = fields.One2many('sped.protocolo.icms.ncm', 'ncm_id', 'Protocolos')
