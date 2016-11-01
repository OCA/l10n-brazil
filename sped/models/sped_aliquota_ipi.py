# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaIPI(models.Model):
    _description = 'Alíquota do IPI'
    _name = 'sped.aliquota.ipi'
    #_table = 'sped_aliquotaipi'
    _rec_name = 'descricao'
    _order = 'al_ipi'

    al_ipi = fields.Porcentagem('Alíquota', required=True)
    md_ipi = fields.Selection(MODALIDADE_BASE_IPI, 'Modalidade da base de cálculo', required=True, default=MODALIDADE_BASE_IPI_ALIQUOTA)
    cst_ipi_entrada = fields.Selection(ST_IPI_ENTRADA, 'Situação tributária nas entradas', required=True, default=ST_IPI_ENTRADA_RECUPERACAO_CREDITO)
    cst_ipi_saida = fields.Selection(ST_IPI_SAIDA, 'Situação tributária do nas saídas', required=True, default=ST_IPI_SAIDA_TRIBUTADA)

    @api.one
    @api.depends('al_ipi', 'md_ipi', 'cst_ipi_entrada', 'cst_ipi_saida')
    def _descricao(self):
        if self.al_ipi == -1:
            self.descricao = 'Não tributado'
        else:
            if self.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
                self.descricao = formata_valor(self.al_ipi or 0) + '%'
            elif self.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
                self.descricao = 'por quantidade, a R$ ' + formata_valor(self.pr_ipi)

            self.descricao += ' - CST ' + self.cst_ipi_entrada
            self.descricao += ' entrada, ' + self.cst_ipi_saida
            self.descricao += ' saída'

    descricao = fields.Char(string='Alíquota do IPI', compute=_descricao, store=True)

    def _valida_al_ipi(self):
        valores = {}
        res = {'value': valores}

        if self.al_ipi or self.md_ipi:
            sql = u"""
            select
                a.id
            from
                sped_aliquota_ipi a
            where
                a.al_ipi = {al_ipi}
                and a.md_ipi = '{md_ipi}'
            """
            sql = sql.format(al_ipi=self.al_ipi, md_ipi=self.md_ipi)

            if self.id or self._origin.id:
                sql += u"""
                    and a.id != {id}
                """
                sql = sql.format(id=self.id or self._origin.id)

            self.env.cr.execute(sql)
            jah_existe = self.env.cr.fetchall()

            if jah_existe:
                raise ValidationError('Alíquota já existe!')

        return res

    @api.one
    @api.constrains('al_ipi', 'md_ipi')
    def constrains_nome(self):
        self._valida_al_ipi()

    @api.onchange('al_ipi', 'md_ipi')
    def onchange_al_ipi(self):
        return self._valida_al_ipi()

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}
        #self.descricao = ''

        #for self in self.browse(cursor, user_id, ids):
            #if self.al_ipi == -1:
                #self.descricao = 'Não tributado'
            #else:
                #if self.md_ipi == MODALIDADE_BASE_IPI_ALIQUOTA:
                    #self.descricao = '%.2f%%' % self.al_ipi
                #elif self.md_ipi == MODALIDADE_BASE_IPI_QUANTIDADE:
                    #self.descricao = 'POR QUANTIDADE, A R$ %.4f%%' % self.al_ipi

                #self.descricao = self.descricao.replace('.', ',').replace(';', ',')

                #self.descricao += ' - CST ENTRADA: %s, CST SAÍDA: %s' % (self.cst_ipi_entrada, self.cst_ipi_saida)

            #retorno[self.id] = self.descricao

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #('al_ipi', '>=', texto),
            #]
        #return procura

    #_rec_name = 'descricao'
    #_order = 'al_ipi'

    #_sql_constraints = [
        #('al_ipi_md_ipi_unique', 'unique (al_ipi, md_ipi)',
        #'A alíquota do IPI não pode se repetir!'),
        #]
