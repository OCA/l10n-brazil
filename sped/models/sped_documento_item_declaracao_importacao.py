# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    INTERMEDIACAO_IMPORTACAO,
    VIA_TRANSPORTE_IMPORTACAO,
)


class DocumentoItemDeclaracaoImportacao(models.Model):
    _description = u'Declaração de Importação do Item do Documento Fiscal'
    _inherit = 'sped.base'
    _name = 'sped.documento.item.declaracao.importacao'

    item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string=u'Item do Documento',
        ondelete='cascade',
        required=True,
    )
    numero_documento = fields.Char(
        string=u'Nº do documento de importação',
        size=12,
    )
    data_registro = fields.Date(
        string=u'Data de registro',
    )
    local_desembaraco = fields.Char(
        string=u'Local do desembaraço',
        size=60,
    )
    uf_desembaraco_id = fields.Many2one(
        comodel_name='sped.estado',
        string=u'Estado do desembaraço',
    )
    data_desembaraco = fields.Date(
        string=u'Data do desembaraço',
    )
    via_trans_internacional = fields.Selection(
        selection=VIA_TRANSPORTE_IMPORTACAO,
        string=u'Via de transporte internacional',
    )
    vr_afrmm = fields.Monetary(
        string=u'Valor do AFRMM',
    )
    forma_importacao = fields.Selection(
        selection=INTERMEDIACAO_IMPORTACAO,
        string=u'Forma de importação',
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Adquirente/encomendante',
    )

    #
    # Quando houver uma única adição, o que é o mais comum,
    # preencher diretamente no registro da DI
    #
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


class DocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    declaracao_ids = fields.One2many(
        comodel_name='sped.documento.item.declaracao.importacao',
        inverse_name='item_id',
        string=u'Declarações de importação',
    )
