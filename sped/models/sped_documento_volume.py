# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo import fields, models
import odoo.addons.decimal_precision as dp


class SpedDocumentoVolume(SpedBase, models.Model):
    _name = b'sped.documento.volume'
    _description = 'Volumes do Documento Fiscal'
    # _order = 'emissao, modelo, data_emissao desc, serie, numero'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento',
        ondelete='cascade',
    )
    especie = fields.Char(
        string='Espécie',
        size=60
    )
    marca = fields.Char(
        string='Marca',
        size=60
    )
    numero = fields.Char(
        string='Número',
        size=60
    )
    quantidade = fields.Integer(
        string='Quantidade',
    )
    peso_liquido = fields.Monetary(
        string='Peso líquido',
        currency_field='currency_peso_id',
    )
    peso_bruto = fields.Monetary(
        string='Peso bruto',
        currency_field='currency_peso_id',
    )
