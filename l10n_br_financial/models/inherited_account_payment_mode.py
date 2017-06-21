# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from ..constantes import (
    TIPO_COBRANCA,
    TIPO_COBRANCA_SPED,
)


class AccountPaymentMode(models.Model):

    _inherit = b'account.payment.mode'

    tipo_cobranca = fields.Selection(
        selection=TIPO_COBRANCA,
    )
    tipo_cobranca_sped = fields.Selection(
        selection=TIPO_COBRANCA_SPED,
    )
