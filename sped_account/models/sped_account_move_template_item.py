# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import UserError
from ..constantes import CAMPO_DOCUMENTO_FISCAL


class SpedAccountMoveTemplateItem(models.Model):
    _name = b'sped.account.move.template.item'
    _description = 'Item do modelo de partidas dobradas'

    template_id = fields.Many2one(
        comodel_name='sped.account.move.template',
        string='Modelo',
        required=True,
        ondelete='cascade',
    )
    campo = fields.Selection(
        selection=CAMPO_DOCUMENTO_FISCAL,
        string='Campo',
        required=True,
    )
    account_debito_id = fields.Many2one(
        comodel_name='account.account',
        string='Débito',
        domain=[('is_brazilian_account', '=', True), ('tipo_sped', '=', 'A')],
    )
    account_credito_id = fields.Many2one(
        comodel_name='account.account',
        string='Crédito',
        domain=[('is_brazilian_account', '=', True), ('tipo_sped', '=', 'A')],
    )
