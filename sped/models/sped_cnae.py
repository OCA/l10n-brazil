# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class CNAE(models.Model):
    _description = 'CNAE'
    _name = 'sped.cnae'
    _order = 'codigo'
    _rec_name = 'cnae'

    codigo = fields.Char('Código', size=7, required=True, index=True)
    descricao = fields.NameChar('Descrição', size=255, required=True, index=True)

    @api.one
    @api.depends('codigo', 'descricao')
    def _cnae(self):
        self.cnae = self.codigo[:4] + '-' + self.codigo[4] + '/' + self.codigo[5:]
        self.cnae += ' - ' + self.descricao

    cnae = fields.Char(string='CNAE', compute=_cnae, store=True)

    #_sql_constraints = [
        #('codigo_unique', 'unique (codigo)', u'O código não pode se repetir!'),
        #]

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += ['|', ('codigo', '=', name), ('descricao', 'ilike', name)]

        return super(CNAE, self).name_search(name=name, args=args, operator=operator, limit=limit)

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if not self.codigo:
            return res

        if self.id:
            cnae_ids = self.search([('codigo', '=', self.codigo), ('id', '!=', self.id)])
        else:
            cnae_ids = self.search([('codigo', '=', self.codigo)])

        if len(cnae_ids) > 0:
            raise ValidationError(u'Código já existe na tabela!')

        return res

    @api.one
    @api.constrains('codigo')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo')
    def onchange_codigo(self):
        return self._valida_codigo()
