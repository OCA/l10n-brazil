# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class NBS(models.Model):
    _description = 'nbs'
    _name = 'sped.nbs'
    _order = 'codigo'
    _rec_name = 'nbs'

    codigo = fields.Char('Código', size=9, required=True, index=True)
    descricao = fields.NameChar('Descrição', size=255, required=True, index=True)
    codigo_formatado = fields.Char(string='nbs', compute='_compute_nbs', store=True)
    nbs = fields.Char(string='nbs', compute='_compute_nbs', store=True)

    @api.depends('codigo', 'descricao')
    def _nbs(self):
        for nbs in self:
            nbs.codigo_formatado = nbs.codigo[0] + '.' + nbs.codigo[1:5] + '.' + nbs.codigo[5:7] + '.' + nbs.codigo[7:]
            nbs.nbs = nbs.codigo_formatado + ' - ' + nbs.descricao[:60]

    @api.depends('codigo')
    def _check_codigo(self):
        for nbs in self:
            if nbs.id:
                nbs_ids = self.search([('codigo', '=', nbs.codigo), ('id', '!=', nbs.id)])
            else:
                nbs_ids = self.search([('codigo', '=', nbs.codigo)])

            if len(nbs_ids) > 0:
                raise ValidationError('Código NBS já existe na tabela!')
