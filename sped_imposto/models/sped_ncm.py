# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from pybrasil.base import mascara

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedNCM(models.Model):
    _name = b'sped.ncm'
    _description = 'NCM'
    _order = 'codigo, ex'
    _rec_name = 'ncm'

    codigo = fields.Char(
        string='Código',
        size=8,
        required=True,
        index=True
    )
    ex = fields.Char(
        string='EX',
        size=2,
        index=True
    )
    descricao = fields.Char(
        string='Descrição',
        size=255,
        required=True,
        index=True
    )
    al_ipi_id = fields.Many2one(
        comodel_name='sped.aliquota.ipi',
        string='Alíquota do IPI'
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade de tributação',
        ondelete='restrict'
    )
    codigo_formatado = fields.Char(
        string='NCM',
        compute='_compute_ncm',
        store=True
    )
    ncm = fields.Char(
        string='NCM',
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

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like', 'ilike'):
            args = list(args or [])
            args = [
                '|',
                ('codigo', '=', name),
                '|',
                ('codigo_formatado', '=', mascara(name, '  .  .  .  ')),
                ('descricao', operator, name),
            ] + args

            ncm_ids = self.search(args, limit=limit)
            return ncm_ids.name_get()

        return super(SpedNCM, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
