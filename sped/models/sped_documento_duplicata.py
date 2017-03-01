# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models


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
    )
    pagamento_id = fields.Many2one(
        comodel_name='sped.documento.pagamento',
        string=u'Pagamento',
        ondelete='cascade',
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

    @api.depends('pagamento_id', 'documento_id')
    def _check_pagamento_id_documento_id(self):
        for duplicata in self:
            if duplicata.pagamento_id:
                if (not duplicata.documento_id):
                    duplicata.documento_id = \
                        duplicata.pagamento_id.documento_id.id
                elif duplicata.documento_id.id != \
                    duplicata.pagamento_id.documento_id.id:
                    duplicata.documento_id = \
                        duplicata.pagamento_id.documento_id.id
