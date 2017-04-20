# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaISS(models.Model):
    _description = 'Alíquota do ISS'
    _name = 'sped.aliquota.iss'
    _rec_name = 'al_iss'
    _order = 'servico_id, municipio_id, al_iss'

    servico_id = fields.Many2one('sped.servico', 'Serviço', ondelete='cascade', required=True)
    municipio_id = fields.Many2one('sped.municipio', 'Município', ondelete='restrict', required=True)
    al_iss = fields.Porcentagem('Alíquota', required=True)
