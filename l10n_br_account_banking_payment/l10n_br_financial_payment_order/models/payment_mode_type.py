# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from openerp import api, fields, models, _

from ..constantes import TIPOS_ORDEM_PAGAMENTO


class PaymentModeType(models.Model):

    _inherit = b'payment.mode.type'

    tipo_pagamento = fields.Selection(
        string="Tipos de Ordem de Pagamento",
        selection=TIPOS_ORDEM_PAGAMENTO,
        help="Tipos de Ordens de Pagamento.",
    )
