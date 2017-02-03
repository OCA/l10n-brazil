# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models


class Base(models.AbstractModel):
    _description = 'Modelo base para campos em Reais e %'
    _name = 'sped.base'

    #
    # Para todos os valores num item de documento fiscal, a moeda é SEMPRE o
    # Real BRL
    # o currency_aliquota_id é para colocar o sinal de % depois dos percetuais
    #
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Moeda',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('base.BRL')
    )
    currency_aliquota_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Percentual',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('sped.SIMBOLO_ALIQUOTA')
    )
    currency_unitario_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Unitário',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('sped.SIMBOLO_VALOR_UNITARIO')
    )

    def _compute_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id
            item.currency_aliquota_id = self.env.ref(
                'sped.SIMBOLO_ALIQUOTA').id
            item.currency_unitario_id = self.env.ref(
                'sped.SIMBOLO_VALOR_UNITARIO').id
