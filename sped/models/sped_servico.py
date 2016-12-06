# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class Servico(models.Model):
    _description = 'Serviço'
    _name = 'sped.servico'
    _order = 'codigo'
    _rec_name = 'servico'

    codigo = fields.Char('Código', size=4, required=True, index=True)
    descricao = fields.NameChar('Descrição', size=400, required=True, index=True)
    codigo_municipio = fields.Char('Código no município', size=9)
    al_iss_ids = fields.One2many('sped.aliquota.iss', 'servico_id', 'Alíquotas de ISS')
    codigo_formatado = fields.Char(string='Servico', compute='_compute_servico', store=True)
    servico = fields.Char(string='Servico', compute='_compute_servico', store=True)

    @api.depends('codigo', 'descricao')
    def _compute_servico(self):
        for servico in self:
            servico.codigo_formatado = servico.codigo[:2] + '.' + servico.codigo[2:]
            servico.servico = servico.codigo_formatado

            servico.servico += ' - ' + servico.descricao[:60]

    @api.depends('codigo')
    def _check_codigo(self):
        for servico in self:
            if servico.id:
                servico_ids = self.search([('codigo', '=', servico.codigo), ('id', '!=', servico.id)])
            else:
                servico_ids = self.search([('codigo', '=', servico.codigo)])

            if len(servico_ids) > 0:
                raise ValidationError('Código de Serviço já existe na tabela!')
