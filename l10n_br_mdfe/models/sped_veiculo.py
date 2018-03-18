# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    TIPO_RODADO,
    TIPO_CARROCERIA
)


class SpedVeiculo(models.Model):

    _inherit = 'sped.veiculo'

    codigo = fields.Char(
        string='Código'
    )
    ciot = fields.Char(
        string='Tipo CIOT',
        help='Também Conhecido como conta frete',
    )
    tipo_rodado = fields.Selection(
        selection=TIPO_RODADO,
        string='Rodado',
    )
    tipo_carroceria = fields.Selection(
        selection=TIPO_CARROCERIA,
        string='Tipo de carroceria',
    )
    tara_kg = fields.Float(
        string='Tara (kg)'
    )
    capacidade_kg = fields.Float(
        string='Capacidade (kg)',
    )
    capacidade_m3 = fields.Float(
        string='Capacidade (m³)'
    )

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            nome = ''
            if record.codigo:
                nome = '['
                nome += record.codigo
                nome += '] '
            nome += record.placa
            res.append((record.id, nome))
        return res