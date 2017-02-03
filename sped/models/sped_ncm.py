# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class NCM(models.Model):
    _description = u'NCM'
    _name = 'sped.ncm'
    _order = 'codigo, ex'
    _rec_name = 'ncm'

    codigo = fields.Char(
        string=u'Código',
        size=8,
        required=True,
        index=True
    )
    ex = fields.Char(
        string=u'EX',
        size=2,
        index=True
    )
    descricao = fields.Char(
        string=u'Descrição',
        size=255,
        required=True,
        index=True
    )
    al_ipi_id = fields.Many2one(
        comodel_name='sped.aliquota.ipi',
        string=u'Alíquota do IPI'
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string=u'Unidade de tributação',
        ondelete='restrict'
    )
    codigo_formatado = fields.Char(
        string=u'NCM',
        compute='_compute_ncm',
        store=True
    )
    ncm = fields.Char(
        string=u'NCM',
        compute='_compute_ncm',
        store=True
    )

    @api.depends('codigo', 'ex', 'descricao', 'al_ipi_id')
    def _compute_ncm(self):
        for ncm in self:
            ncm.codigo_formatado = (
                ncm.codigo[:2] +
                '.' +
                ncm.codigo[2:4] +
                '.' + ncm.codigo[4:6] +
                '.' + ncm.codigo[6:]
            )
            ncm.ncm = ncm.codigo_formatado

            if ncm.ex:
                ncm.ncm += '-ex' + ncm.ex

            ncm.ncm += ' - ' + ncm.descricao[:60]

    @api.depends('codigo', 'ex')
    def _check_codigo(self):
        for ncm in self:
            if ncm.id:
                ncm_ids = self.search([
                    ('codigo', '=', ncm.codigo),
                    ('ex', '=', ncm.ex),
                    ('id', '!=', ncm.id)
                ])
            else:
                ncm_ids = self.search([
                    ('codigo', '=', ncm.codigo),
                    ('ex', '=', ncm.ex)
                ])

            if len(ncm_ids) > 0:
                raise ValidationError('Código NCM já existe na tabela!')
