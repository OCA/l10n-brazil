# -*- coding: utf-8 -*-


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
    #cest_ids = fields.Many2many('sped.cest', 'tabela_servico_cest', 'servico_id', 'cest_id', 'Códigos CEST')
    al_iss_ids = fields.One2many('sped.aliquota.iss', 'servico_id', 'Alíquotas de ISS')

    @api.one
    @api.depends('codigo', 'descricao')
    def _servico(self):
        self.codigo_formatado = self.codigo[:2] + '.' + self.codigo[2:]
        self.servico = self.codigo_formatado

        self.servico += ' - ' + self.descricao[:60]

    codigo_formatado = fields.Char(string='Servico', compute=_servico, store=True)
    servico = fields.Char(string='Servico', compute=_servico, store=True)

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if (not self.codigo):
            return res

        if self.id:
            servico_ids = self.search([('codigo', '=', self.codigo), ('id', '!=', self.id)])
        else:
            servico_ids = self.search([('codigo', '=', self.codigo)])

        if len(servico_ids) > 0:
            raise ValidationError('Código já existe na tabela!')

        return res

    @api.one
    @api.constrains('codigo')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo')
    def onchange_codigo(self):
        return self._valida_codigo()
