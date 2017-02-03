# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CEST(models.Model):
    _description = u'CEST'
    _name = 'sped.cest'
    _order = 'codigo'
    _rec_name = 'cest'

    codigo = fields.Char(
        string=u'Código',
        size=7,
        required=True,
        index=True,
    )
    descricao = fields.Text(
        string=u'Descrição',
        required=True,
    )
    codigo_formatado = fields.Char(
        string=u'CEST',
        compute='_compute_cest',
        store=True,
    )
    cest = fields.Char(
        string=u'CEST',
        compute='_compute_cest',
        store=True,
    )

    @api.depends('codigo', 'descricao')
    def _compute_cest(self):
        for cest in self:
            cest.codigo_formatado = (
                cest.codigo[:2] + '.' +
                cest.codigo[2:5] + '.' +
                cest.codigo[5:]
            )
            cest.cest = cest.codigo_formatado
            cest.cest += ' - ' + cest.descricao[:60]

    @api.depends('codigo')
    def _check_codigo(self):
        for cest in self:
            if cest.id:
                cest_ids = self.search(
                    [('codigo', '=', cest.codigo), ('id', '!=', cest.id)])
            else:
                cest_ids = self.search([('codigo', '=', cest.codigo)])

            if len(cest_ids) > 0:
                raise ValidationError(u'Código CEST já existe na tabela!')
