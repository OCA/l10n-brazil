# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    TIPO_TRANSPORTADOR,
    MODALIDADE_TRANSPORTE,
    TIPO_EMITENTE,
)


class SpedOperacao(models.Model):

    _inherit = b'sped.operacao'

    tipo_emitente = fields.Selection(
        selection=TIPO_EMITENTE,
        string='Tipo de emitente',
    )

    tipo_transportador = fields.Selection(
        selection=TIPO_TRANSPORTADOR,
        string='Tipo do transportador'
    )
    modalidade_transporte = fields.Selection(
        selection=MODALIDADE_TRANSPORTE,
        string='Modalidade',
    )

