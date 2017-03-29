# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NBS(models.Model):
    _description = u'nbs'
    _name = 'sped.nbs'
    _order = 'codigo'
    _rec_name = 'nbs'

    codigo = fields.Char(
        string=u'Código',
        size=9,
        required=True,
        index=True
    )
    descricao = fields.Char(
        string=u'Descrição',
        size=255,
        required=True,
        index=True
    )
    codigo_formatado = fields.Char(
        string=u'nbs',
        compute='_compute_nbs',
        store=True
    )
    nbs = fields.Char(
        string=u'nbs',
        compute='_compute_nbs',
        store=True
    )

    @api.depends('codigo', 'descricao')
    def _compute_nbs(self):
        for nbs in self:
            nbs.codigo_formatado = (
                nbs.codigo[0] +
                '.' +
                nbs.codigo[1:5] +
                '.' +
                nbs.codigo[5:7] +
                '.' +
                nbs.codigo[7:]
            )
            nbs.nbs = nbs.codigo_formatado + ' - ' + nbs.descricao[:60]

    @api.depends('codigo')
    def _check_codigo(self):
        for nbs in self:
            if nbs.id:
                nbs_ids = self.search([
                    ('codigo', '=', nbs.codigo),
                    ('id', '!=', nbs.id),
                ])
            else:
                nbs_ids = self.search([
                    ('codigo', '=', nbs.codigo),
                ])

            if len(nbs_ids) > 0:
                raise ValidationError(u'Código NBS já existe na tabela!')
