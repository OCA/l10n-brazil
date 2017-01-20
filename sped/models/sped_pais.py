# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira
# <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class Pais(models.Model):

    _description = u'País'

    _name = 'sped.pais'
    _rec_name = 'nome'
    _order = 'nome'
    _inherits = {'res.country': 'country_id'}

    country_id = fields.Many2one(
        comodel_name='res.country',
        string=u'Country original',
        ondelete='restrict',
        required=True
    )
    codigo_bacen = fields.Char(
        string=u'Código BANCO CENTRAL',
        size=4,
        index=True,
    )
    codigo_siscomex = fields.Char(
        string=u'Código SISCOMEX',
        size=3,
    )
    nome = fields.Char(
        string=u'Nome',
        size=60,
        index=True,
    )
    iso_3166_alfa_2 = fields.Char(
        string=u'Código ISO 3166',
        size=2,
        index=True
    )
