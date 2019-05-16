# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _


class HrInformativoAtividadeTrabalho(models.Model):
    _name = 'hr.informativo.atividade.trabalho'
    _description = u'Condições Ambientais de Trabalho - Fator de Risco'
    _rec_name = 'desc_atividade'

    desc_atividade = fields.Text(
        string=u'Descrição das Atividades',
    )
    cod_atividade_ids = fields.Many2many(
        string=u'Código(s) da(s) Atividade(s)',
        comodel_name='sped.atividades_perigosas_insalubres',
        relation='informativo_atividade_atividades_perigosas_insalubres_rel',
        column1='hr_informativo_atividade_trabalho_id',
        column2='sped_atividades_perigosas_insalubres_id',
    )
    condicao_ambiente_trabalho_id = fields.One2many(
        comodel_name='hr.condicao.ambiente.trabalho',
        inverse_name='hr_atividade_id',
    )
