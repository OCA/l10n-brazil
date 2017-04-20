# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from openerp import models, fields, api
from odoo.exceptions import UserError, ValidationError


class NaturezaOperacao(models.Model):
    _name = 'sped.natureza.operacao'
    _description = 'Naturezas de operação fiscal'
    _rec_name = 'nome'
    _order = 'nome'

    codigo = fields.UpperChar('Código', size=10, required=True, index=True)
    nome = fields.NameChar('Nome', size=60, required=True, index=True)

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'O código da natureza de operação fiscal não pode se repetir!'),
        ('nome_unique', 'unique(nome)', 'O nome da natureza de operação fiscal não pode se repetir!'),
    ]

    def _valida_codigo(self):
        valores = {}
        res = {'value': valores}

        if not (self.codigo or self.nome):
            return res

        if self.id:
            if self.codigo:
                cest_ids = self.search([('codigo', '=', self.codigo), ('id', '!=', self.id)])
            elif self.nome:
                cest_ids = self.search([('nome', '=', self.codigo), ('id', '!=', self.id)])
        else:
            cest_ids = self.search([('codigo', '=', self.codigo)])


        sql = u"""
        select
            a.id
        from
            sped_natureza_operacao a
        where
        """

        if self.codigo:
            sql += """
                trim(upper(unaccent(a.codigo))) = trim(upper(unaccent('{codigo}')))
            """
            sql = sql.format(codigo=self.codigo.strip())

        elif self.nome:
            sql += """
                trim(upper(unaccent(a.nome))) = trim(upper(unaccent('{nome}')))
            """
            sql = sql.format(nome=self.nome.strip())

        if self.id or self._origin.id:
            sql += u"""
                and a.id != {id}
            """
            sql = sql.format(id=self.id or self._origin.id)

        self.env.cr.execute(sql)
        jah_existe = self.env.cr.fetchall()

        if jah_existe:
            raise ValidationError(u'Natureza de operação fiscal já existe!')

        return res

    @api.one
    @api.constrains('codigo', 'nome')
    def constrains_codigo(self):
        self._valida_codigo()

    @api.onchange('codigo', 'nome')
    def onchange_codigo(self):
        return self._valida_codigo()
