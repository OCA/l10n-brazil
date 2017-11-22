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

    lote_numero = fields.Char(
        string='Lote nº',
    )



class DocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    rastreabilidade_ids = fields.One2many(
        comodel_name='sped.documento.item.rastreabilidade',
        inverse_name='item_id',
        string='Restreabilidade',
    )
