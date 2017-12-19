# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import SITUACAO_NFE


class SpedOperacaoSubsequente(models.Model):

    _name = b'sped.operacao.subsequente'
    _description = 'Sped Operacao Subsequente'
    _rec_name = 'operacao_id'
    _order = 'sequence'

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Gives the sequence order when displaying a list"
    )
    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação de origem',
        required=True,
        ondelete='cascade',

    )
    operacao_subsequente_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação a ser realizada',
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
    )
    situacao_geracao = fields.Selection(
        string="Situaçao Geraçao",
        selection=SITUACAO_NFE,
    )
    referenciar_documento = fields.Boolean(
        string="Refenciar documento de origem",
    )
