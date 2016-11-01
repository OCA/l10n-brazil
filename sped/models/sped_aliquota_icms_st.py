# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaICMSST(models.Model):
    _description = 'Alíquota do ICMS ST'
    _name = 'sped.aliquota.icms.st'
    #_table = 'sped_aliquotaicmsst'
    _rec_name = 'descricao'
    _order = 'al_icms, md_icms, pr_icms, rd_icms, rd_mva'

    al_icms = fields.Porcentagem('Alíquota', required=True)
    md_icms = fields.Selection(MODALIDADE_BASE_ICMS_ST, 'Modalidade da base de cálculo', required=True, default=MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO)
    pr_icms = fields.Quantidade('Parâmetro da base de cálculo', required=True,
            help='A margem de valor agregado, ou o valor da pauta/preço tabelado máximo/lista, de acordo com o definido na modalidade da base de cálculo.')
    rd_icms = fields.Porcentagem('Percentual de redução da alíquota')
    rd_mva = fields.Porcentagem('Percentual de redução do MVA para o SIMPLES')

    @api.one
    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms')
    def _descricao(self):
        if self.al_icms == -1:
            self.descricao = 'Não tributado'
        else:
            self.descricao = formata_valor(self.al_icms or 0) + '%'

            if self.md_icms == MODALIDADE_BASE_ICMS_ST_PRECO_TABELADO_MAXIMO:
                self.descricao += ', por preço máximo'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEGATIVA:
                self.descricao += ', por lista negativa'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_POSITIVA:
                self.descricao += ', por lista positiva'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_LISTA_NEUTRA:
                self.descricao += ', por lista neutra'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                self.descricao += ', por MVA'
            elif self.md_icms == MODALIDADE_BASE_ICMS_ST_PAUTA:
                self.descricao += ', por pauta'

            if self.pr_icms:
                if self.md_icms == MODALIDADE_BASE_ICMS_ST_MARGEM_VALOR_AGREGADO:
                    self.descricao += ' de ' + formata_valor(self.pr_icms, casas_decimais=4) + '%'
                else:
                    self.descricao += ' de R$ ' + formata_valor(self.pr_icms, casas_decimais=4)

            if self.rd_icms != 0:
                self.descricao += ', com redução de ' + formata_valor(self.rd_icms) + '%'

            if self.rd_mva != 0:
                self.descricao += ', com MVA reduzido em ' + formata_valor(self.rd_mva) + '% para o SIMPLES'

    descricao = fields.Char(string='Alíquota do ICMS ST', compute=_descricao, store=False)

    def _valida_al_icms(self):
        valores = {}
        res = {'value': valores}

        if self.al_icms or self.md_icms or self.pr_icms or self.rd_icms or self.rd_mva:
            sql = u"""
            select
                a.id
            from
                sped_aliquota_icms_st a
            where
                a.al_icms = {al_icms}
                and a.md_icms = '{md_icms}'
                and a.pr_icms = {pr_icms}
                and a.rd_icms = {rd_icms}
                and a.rd_mva = {rd_mva}
            """
            sql = sql.format(al_icms=self.al_icms, md_icms=self.md_icms, pr_icms=self.pr_icms, rd_icms=self.rd_icms, rd_mva=self.rd_mva)

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
    @api.constrains('al_icms', 'md_icms', 'pr_icms', 'rd_icms', 'rd_mva')
    def constrains_nome(self):
        self._valida_al_icms()

    @api.onchange('al_icms', 'md_icms', 'pr_icms', 'rd_icms', 'rd_mva')
    def onchange_al_icms(self):
        return self._valida_al_icms()
