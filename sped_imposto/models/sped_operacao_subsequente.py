# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    SITUACAO_NFE,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
)


SITUACAO_SUBSEQUENTE = (
    ('manual', 'Manualmente'),
    ('nota_de_cupom', 'Gerar Nota Fiscal de Cupons Fiscais'),
    ('nota_de_remessa', 'Gerar Nota Fiscal de Remessa'),
)

OPERACAO_SUBSEQUENTE = SITUACAO_NFE + SITUACAO_SUBSEQUENTE

""" Devemos ficar atentos pois algumas operações subsequentes não geram lançamentos
financeiros"""


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
        string='Participante'
    )
    situacao_geracao = fields.Selection(
        string="Situaçao Geraçao",
        selection=OPERACAO_SUBSEQUENTE,
        required=True,
        default='manual',
    )
    referenciar_documento = fields.Boolean(
        string="Refenciar documento de origem",
    )

    @api.multi
    def _confirma_geracao(self, documento):
        """ Dado um documento fiscal verificamos se podemos gerar a operação
        :param documento:
        :return: True permitindo a geração
        """
        result = False

        if self.situacao_geracao in [x for x, y in SITUACAO_SUBSEQUENTE]:
            cupom = documento.filtered(lambda documento: documento.modelo in (
                MODELO_FISCAL_CFE,
                MODELO_FISCAL_NFCE,
                MODELO_FISCAL_CUPOM_FISCAL_ECF,
            ))
            if cupom:
                result = True
        elif documento.situacao_nfe == self.situacao_geracao:
            result = True

        return result
