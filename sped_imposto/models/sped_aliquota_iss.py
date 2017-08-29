# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo import fields, models


class SpedAliquotaISS(SpedBase, models.Model):
    _name = b'sped.aliquota.iss'
    _description = 'Alíquotas do ISS'
    _rec_name = 'al_iss'
    _order = 'servico_id, municipio_id, al_iss'

    servico_id = fields.Many2one(
        'sped.servico',
        string='Serviço',
        ondelete='cascade',
        required=True,
    )
    municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Município',
        ondelete='restrict',
        required=True,
    )
    al_iss = fields.Monetary(
        string='Alíquota',
        required=True,
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    codigo = fields.Char(
        string='Código específico',
        size=10,
    )
