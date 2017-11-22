# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo.addons.l10n_br_base.constante_tributaria import (
    INTERMEDIACAO_IMPORTACAO,
    VIA_TRANSPORTE_IMPORTACAO,
)


class SpedDocumentoItemRestreabilidade(SpedBase, models.Model):
    _name = b'sped.documento.item.rastreabilidade'
    _description = 'Restreabilidade do Item do Documento Fiscal'

    item_id = fields.Many2one(
        comodel_name='sped.documento.item',
        string='Item do Documento',
        ondelete='cascade',
        required=True,
    )
    currency_unidade_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade',
        related='item_id.currency_unidade_id',
        readonly=True,
    )
    numero = fields.Char(
        string='Lote nº',
        size=20,
        required=True,
    )
    quantidade = fields.Monetary(
        string='Quantidade',
        default=1,
        currency_field='currency_unidade_id',
        required=True,
    )
    data_fabricacao = fields.Date(
        string='Data de fabricação',
        required=True,
    )
    data_validade = fields.Date(
        string='Data de validade',
        required=True,
    )
    codigo_agregacao = fields.Char(
        string='Código de agregação',
        size=20,
    )


class DocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    rastreabilidade_ids = fields.One2many(
        comodel_name='sped.documento.item.rastreabilidade',
        inverse_name='item_id',
        string='Restreabilidade',
    )
