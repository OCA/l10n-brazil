# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira
# <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class SpedPais(models.Model):
    _name = b'sped.pais'
    _description = 'Países'
    _rec_name = 'nome'
    _order = 'nome'
    _inherits = {'res.country': 'country_id'}

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country original',
        ondelete='restrict',
        required=True,
    )
    codigo_bacen = fields.Char(
        string='Código BANCO CENTRAL',
        size=4,
        index=True,
    )
    codigo_siscomex = fields.Char(
        string='Código SISCOMEX',
        size=3,
    )
    nome = fields.Char(
        string='Nome',
        size=60,
        index=True,
    )
    iso_3166_alfa_2 = fields.Char(
        string='Código ISO 3166',
        size=2,
        index=True,
    )
