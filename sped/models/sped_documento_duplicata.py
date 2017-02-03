# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models


class DocumentoDuplicata(models.Model):
    _description = u'Duplicata do Documento Fiscal'
    _inherit = 'sped.base'
    _name = 'sped.documento.duplicata'
    _order = 'documento_id, data_vencimento'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento',
        ondelete='cascade',
        required=True,
    )
    numero = fields.Char(
        string=u'Número',
        size=60,
        required=True,
    )
    data_vencimento = fields.Date(
        string=u'Data de vencimento',
        required=True,
    )
    valor = fields.Monetary(
        string=u'Valor',
        digits=(18, 2),
        required=True,
    )
