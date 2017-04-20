# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class CEST(models.Model):
    _description = 'CEST'
    _name = 'sped.cest'
    _order = 'codigo'
    _rec_name = 'cest'

    codigo = fields.Char('Código', size=7, required=True, index=True)
    descricao = fields.NameChar('Descrição', size=1500, required=True, index=True)

    @api.one
    @api.depends('codigo', 'descricao')
    def _cest(self):
        self.codigo_formatado = self.codigo[:2] + '.' + self.codigo[2:5] + '.' + self.codigo[5:]
        self.cest = self.codigo_formatado
        self.cest += ' - ' + self.descricao[:60]

    codigo_formatado = fields.Char(string='CEST', compute=_cest, store=True)
    cest = fields.Char(string='CEST', compute=_cest, store=True)

    #_sql_constraints = [
        #('codigo_unique', 'unique (codigo)', u'O código não pode se repetir!'),
        #]

    #def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=100):
        #if name and operator in ('=', 'ilike', '=ilike', 'like'):
            #if operator != '=':
                #name = name.strip().replace(' ', '%')

            #ids = self.search(cr, uid, [
                #'|',
                #('codigo', '=', name),
                #('descricao', 'ilike', name),
                #] + args, limit=limit, context=context)

            #if ids:
                #return self.name_get(cr, uid, ids, context)

        #return super(CEST, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if not self.codigo:
            return res

        if self.id:
            cest_ids = self.search([('codigo', '=', self.codigo), ('id', '!=', self.id)])
        else:
            cest_ids = self.search([('codigo', '=', self.codigo)])

        if len(cest_ids) > 0:
            raise ValidationError(u'Código já existe na tabela!')

        return res

    @api.one
    @api.constrains('codigo')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo')
    def onchange_codigo(self):
        return self._valida_codigo()
