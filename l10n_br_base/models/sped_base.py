# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, data_hora_horario_brasilia

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedBase(object):
    #
    # Para todos os valores num item de documento fiscal, a moeda é SEMPRE o
    # Real BRL
    # o currency_aliquota_id é para colocar o sinal de % depois dos percetuais
    #
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('base.BRL'),
    )
    currency_aliquota_id = fields.Many2one(
        comodel_name='res.currency',
        string='Percentual',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('l10n_br_base.SIMBOLO_ALIQUOTA'),
        context={'only_currencies': False},
        domain=[['is_symbol', '=', True]],
    )
    currency_aliquota_rateio_id = fields.Many2one(
        comodel_name='res.currency',
        string='Percentual',
        compute='_compute_currency_id',
        default=lambda self:
            self.env.ref('l10n_br_base.SIMBOLO_ALIQUOTA_RATEIO'),
        context={'only_currencies': False},
        domain=[['is_symbol', '=', True]],
    )
    currency_unitario_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unitário',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref(
            'l10n_br_base.SIMBOLO_VALOR_UNITARIO'),
        context={'only_currencies': False},
        domain=[['is_symbol', '=', True]],
    )
    currency_peso_id = fields.Many2one(
        comodel_name='res.currency',
        string='Peso',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('l10n_br_base.SIMBOLO_PESO'),
        context={'only_currencies': False},
        domain=[['is_symbol', '=', True]],
    )

    def _compute_currency_id(self):
        for item in self:
            item.currency_id = self.env.ref('base.BRL').id
            item.currency_aliquota_id = self.env.ref(
                'l10n_br_base.SIMBOLO_ALIQUOTA').id
            item.currency_aliquota_rateio_id = self.env.ref(
                'l10n_br_base.SIMBOLO_ALIQUOTA_RATEIO').id
            item.currency_unitario_id = self.env.ref(
                'l10n_br_base.SIMBOLO_VALOR_UNITARIO').id
            item.currency_peso_id = self.env.ref(
                'l10n_br_base.SIMBOLO_PESO').id

    def _separa_data_hora(self, data_hora_odoo):
        data_hora = data_hora_horario_brasilia(
            parse_datetime(data_hora_odoo + ' UTC'))
        data = str(data_hora)[:10]
        hora = str(data_hora)[11:19]
        return data, hora
