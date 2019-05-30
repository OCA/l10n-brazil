# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models

ORDEM_EXAME = [
    ('1', 'Inicial'),
    ('2', 'Sequencial'),
]

IND_RESULTADO = [
    ('1', 'Normal'),
    ('2', 'Alterado'),
    ('3', u'Estável'),
    ('4', 'Agravamento'),
]


class HrExameASO(models.Model):
    _name = 'hr.exame.aso'
    _description = u'Exame ASO'

    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
    )
    contract_id = fields.Many2one(
        string=u'Contrato',
        comodel_name='hr.contract',
    )
    data_exame = fields.Date(
        string=u'Data Exame',
        help=u'Nome Layout: dtExm - Data do exame realizado.'
    )
    procedimento_realizado = fields.Many2one(
        string=u'Procedimento Realizado',
        comodel_name='sped.procedimentos_diagnosticos',
        help=u'Nome Layout: procRealizado - Tamanho: Até 4 Caracteres - Código'
             u' do procedimento diagnóstico constante da Tabela 27.'
    )
    obs_procedimento = fields.Text(
        string=u'Observações',
        size=999,
        help=u'Nome Layout: obsProc - Tamanho: Até 999 Caracteres - Observação'
             u' sobre o procedimento diagnóstico realizado.'
    )
    ordem_exame = fields.Selection(
        string=u'Ordem',
        selection=ORDEM_EXAME,
        help=u'Nome Layout: ordExame - Tamanho: Até 1 Caracteres - Ordem do'
             u' Exame: 1 - Inicial; 2 - Sequencial.',
    )
    indicacao_resultado = fields.Selection(
        string=u'Indicação do Resultado',
        selection=IND_RESULTADO,
        help=u'Nome Layout: indResult - Tamanho: Até 1 Caracteres - Indicação'
             u' dos Resultados: 1 - Normal; 2 - Alterado; '
             u'3 - Estável; 4 - Agravamento.',
    )
    hr_saude_trabalhador_id = fields.Many2one(
        comodel_name='hr.saude.trabalhador',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - {} - {}'.format(
                record.procedimento_realizado.nome, record.data_exame,
                record.contract_id.name
            )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrExameASO, self).fields_view_get(
            view_id, view_type, toolbar=toolbar, submenu=False)

        return res
