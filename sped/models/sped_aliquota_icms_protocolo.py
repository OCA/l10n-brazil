# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.valor import formata_valor


class AliquotaICMSProprio(models.Model):
    _description = 'Alíquota do ICMS próprio'
    _name = 'sped.aliquota.icms.proprio'
    #_table = 'sped_aliquotaicmsproprio'
    _rec_name = 'descricao'
    _order = 'al_icms'

    al_icms = fields.Porcentagem('Alíquota', required=True)
    md_icms = fields.Selection(MODALIDADE_BASE_ICMS_PROPRIO, 'Modalidade da base de cálculo', required=True, default=MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO)
    pr_icms = fields.Quantidade('Parâmetro da base de cálculo',
            help='A margem de valor agregado, ou o valor da pauta/preço tabelado máximo, de acordo com o definido na modalidade da base de cálculo.')
    rd_icms = fields.Porcentagem('Percentual de redução da alíquota')
    importado = fields.Boolean('Padrão para produtos importados?')

    @api.one
    @api.depends('al_icms', 'md_icms', 'pr_icms', 'rd_icms', 'importado')
    def _descricao(self):
        if self.al_icms == -1:
            self.descricao = 'Não tributado'
        else:
            self.descricao = formata_valor(self.al_icms or 0) + '%'

            if self.md_icms != MODALIDADE_BASE_ICMS_PROPRIO_VALOR_OPERACAO:
                if self.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_MARGEM_VALOR_AGREGADO:
                    self.descricao += ', por MVA de ' + formata_valor(self.pr_icms, casas_decimais=4) + '%'
                elif self.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_PAUTA:
                    self.descricao += ', por pauta de R$ ' + formata_valor(self.pr_icms, casas_decimais=4)
                elif self.md_icms == MODALIDADE_BASE_ICMS_PROPRIO_PRECO_TABELADO_MAXIMO:
                    self.descricao += ', por preço máximo de R$ ' + formata_valor(self.pr_icms, casas_decimais=4)

            if self.rd_icms != 0:
                self.descricao += ', com redução de ' + formata_valor(self.rd_icms) + '%'

            if self.importado:
                self.descricao += ' (padrão para importados)'

    descricao = fields.Char(string='Alíquota do ICMS próprio', compute=_descricao, store=True)

    def _valida_al_icms(self):
        valores = {}
        res = {'value': valores}

        if self.al_icms or self.md_icms or self.rd_icms:
            sql = u"""
            select
                a.id
            from
                sped_aliquota_icms_proprio a
            where
                a.al_icms = {al_icms}
                and a.md_icms = '{md_icms}'
                and a.rd_icms = {rd_icms}
            """
            sql = sql.format(al_icms=self.al_icms, md_icms=self.md_icms, rd_icms=self.rd_icms)

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
    @api.constrains('al_icms', 'md_icms', 'rd_icms')
    def constrains_nome(self):
        self._valida_al_icms()

    @api.onchange('al_icms', 'md_icms', 'rd_icms')
    def onchange_al_icms(self):
        return self._valida_al_icms()
