# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo import fields, models


class SpedDocumentoItemDeclaracaoImportacaoAdicao(SpedBase, models.Model):
    _name = b'sped.documento.item.declacarao.importacao.adicao'
    _description = 'Adições da Declaração de Importação do Item do ' \
                   'Documento Fiscal'

    declaracao_id = fields.Many2one(
        comodel_name='sped.documento.item.declacarao.importacao',
        string='Declaração de Importação do Item do Documento Fiscal',
        ondelete='cascade',
        required=True,
    )
    numero_adicao = fields.Integer(
        string='Nº da adição',
        default=1,
    )
    sequencial = fields.Integer(
        string='Sequencial',
        default=1,
    )
    vr_desconto = fields.Monetary(
        string='Valor do desconto',
    )
    numero_drawback = fields.Integer(
        string='Nº drawback',
    )
