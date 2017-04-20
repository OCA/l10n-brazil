# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaPISCOFINS(models.Model):
    _description = 'Alíquota do PIS-COFINS'
    _name = 'sped.aliquota.pis.cofins'
    #_table = 'sped_aliquotapiscofins'
    _rec_name = 'descricao'
    _order = 'al_pis, al_cofins'

    al_pis = fields.Porcentagem('Alíquota do PIS', required=True)
    al_cofins = fields.Porcentagem('Alíquota da COFINS', required=True)
    md_pis_cofins = fields.Selection(MODALIDADE_BASE_PIS, 'Modalidade da base de cálculo', required=True, default=MODALIDADE_BASE_PIS_ALIQUOTA)
    cst_pis_cofins_entrada = fields.Selection(ST_PIS_ENTRADA, 'Situação tributária nas entradas', required=True, default=ST_PIS_CRED_EXCL_TRIB_MERC_INTERNO)
    cst_pis_cofins_saida = fields.Selection(ST_PIS_SAIDA, 'Situação tributária nas saída', required=True, default=ST_PIS_TRIB_NORMAL)
    codigo_justificativa = fields.Char('Código da justificativa', size=10)

    @api.one
    @api.depends('al_pis', 'al_cofins', 'md_pis_cofins', 'cst_pis_cofins_entrada', 'cst_pis_cofins_saida', 'codigo_justificativa')
    def _descricao(self):
        if self.al_pis == -1:
            self.descricao = 'Não tributado'
        else:
            if self.md_pis_cofins == MODALIDADE_BASE_PIS_ALIQUOTA:
                self.descricao = 'PIS ' + formata_valor(self.al_pis or 0) + '%'
                self.descricao += '; COFINS ' + formata_valor(self.al_cofins or 0) + '%'

            elif self.md_pis_cofins == MODALIDADE_BASE_PIS_QUANTIDADE:
                self.descricao = 'por quantidade, PIS a R$ ' + formata_valor(self.al_pis)
                self.descricao += '; COFINS a R$ ' + formata_valor(self.al_cofins)

            self.descricao += ' - CST ' + self.cst_pis_cofins_entrada
            self.descricao += ' entrada, ' + self.cst_pis_cofins_saida
            self.descricao += ' saída'

            if self.codigo_justificativa:
                self.descricao += ' - justificativa '
                self.descricao += self.codigo_justificativa

    descricao = fields.Char(string='Alíquota do PIS-COFINS', compute=_descricao, store=True)

    def _valida_al_pis(self):
        valores = {}
        res = {'value': valores}

        if self.al_pis or self.al_cofins or self.md_pis_cofins or self.cst_pis_cofins_entrada or self.cst_pis_cofins_saida or self.codigo_justificativa:
            sql = u"""
            select
                a.id
            from
                sped_aliquota_pis_cofins a
            where
                a.al_pis = {al_pis}
                and a.al_cofins = {al_cofins}
                and a.md_pis_cofins = '{md_pis_cofins}'
                and a.cst_pis_cofins_entrada = '{cst_pis_cofins_entrada}'
                and a.cst_pis_cofins_saida = '{cst_pis_cofins_saida}'
                and a.codigo_justificativa = '{codigo_justificativa}'
            """
            sql = sql.format(al_pis=self.al_pis, al_cofins=self.al_cofins, md_pis_cofins=self.md_pis_cofins, cst_pis_cofins_entrada=self.cst_pis_cofins_entrada, cst_pis_cofins_saida=self.cst_pis_cofins_saida, codigo_justificativa=self.codigo_justificativa)

            if self.id or self._origin.id:
                sql += u"""
                    and a.id != {id}
                """
                sql = sql.format(id=self.id or self._origin.id)

            self.env.cr.execute(sql)
            jah_existe = self.env.cr.fetchall()

            if jah_existe:
                raise ValidationError('Alíquotas já existem!')

        return res

    @api.one
    @api.constrains('al_pis', 'al_cofins', 'md_pis_cofins', 'cst_pis_cofins_entrada', 'cst_pis_cofins_saida', 'codigo_justificativa')
    def constrains_nome(self):
        self._valida_al_pis()

    @api.onchange('al_pis', 'al_cofins', 'md_pis_cofins', 'cst_pis_cofins_entrada', 'cst_pis_cofins_saida', 'codigo_justificativa')
    def onchange_al_pis(self):
        return self._valida_al_pis()
