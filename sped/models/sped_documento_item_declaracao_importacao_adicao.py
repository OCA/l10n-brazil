# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models


class DocumentoItemDeclaracaoImportacaoAdicao(models.Model):
    _description = u'Adição da Declaração de Importação do Item do Documento' \
                    ' Fiscal'
    _inherit = 'sped.base'
    _name = 'sped.documento.item.declaracao.importacao.adicao'

    declaracao_id = fields.Many2one(
        comodel_name='sped.documento.item.declaracao.importacao',
        string=u'Declaração de Importação do Item do Documento',
        ondelete='cascade',
        required=True,
    )
    numero_adicao = fields.Integer(
        string=u'Nº da adição',
        default=1,
    )
    sequencial = fields.Integer(
        string=u'Sequencial',
        default=1,
    )
    vr_desconto = fields.Monetary(
        string=u'Valor do desconto',
    )
    numero_drawback = fields.Integer(
        string=u'Nº drawback',
    )


class DocumentoItemDeclaracaoImportacao(models.Model):
    _inherit = 'sped.documento.item.declaracao.importacao'

    adicao_ids = fields.One2many(
        comodel_name='sped.documento.item.declaracao.importacao.adicao',
        inverse_name='declaracao_id',
        string=u'Adições',
    )
