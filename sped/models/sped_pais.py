# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class Pais(models.Model):
    _description = 'País'
    _name = 'sped.pais'
    _rec_name = 'nome'
    _order = 'nome'

    codigo_bacen = fields.Char('Código BANCO CENTRAL', size=4, index=True)
    codigo_siscomex = fields.Char('Código SISCOMEX', size=3)
    nome = fields.NameChar('Nome', size=60, index=True)
    iso_3166_alfa_2 = fields.Char('Código ISO 3166', size=2, index=True)
