# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class nbs(models.Model):
    _description = 'nbs'
    _name = 'sped.nbs'
    _order = 'codigo'
    _rec_name = 'nbs'

    codigo = fields.Char('Código', size=9, required=True, index=True)
    descricao = fields.NameChar('Descrição', size=255, required=True, index=True)

    @api.one
    @api.depends('codigo', 'descricao')
    def _nbs(self):
        self.codigo_formatado = self.codigo[0] + '.' + self.codigo[1:5] + '.' + self.codigo[5:7] + '.' + self.codigo[7:]

        self.nbs = self.codigo_formatado + ' - ' + self.descricao[:60]

    codigo_formatado = fields.Char(string='nbs', compute=_nbs, store=True)
    nbs = fields.Char(string='nbs', compute=_nbs, store=True)

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if (not self.codigo):
            return res

        if self.id:
            nbs_ids = self.search([('codigo', '=', self.codigo), ('id', '!=', self.id)])
        else:
            nbs_ids = self.search([('codigo', '=', self.codigo)])

        if len(nbs_ids) > 0:
            raise ValidationError('Código já existe na tabela!')

        return res

    @api.one
    @api.constrains('codigo')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo')
    def onchange_codigo(self):
        return self._valida_codigo()
