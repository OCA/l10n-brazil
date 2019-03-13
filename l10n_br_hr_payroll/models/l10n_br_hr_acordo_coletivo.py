# -*- coding: utf-8 -*-
# Copyright (C) 2019  Luiz Felipe do Divino - ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, fields

TIPO_ACORDOS = [
    ('A', 'Acordo Coletivo de Trabalho'),
    ('B', 'Legislação Federal, Estadual, Municipal ou Distrital'),
    ('C', 'Convenção Coletiva de Trabalho'),
    ('D', 'Setença Normativa - Dissídio'),
    ('E', 'Conversão de Licença Saúde em Acidente de Trabalho'),
    ('F', 'Outras verbas de natureza salarial ou não salarial devidas após o desligamento'),
]


class L10nBrHrAcordoColetivo(models.Model):
    _name = 'l10n.br.hr.acordo.coletivo'

    name = fields.Char(
        string='name',
        compute='_compute_name'
    )
    data_assinatura_acordo = fields.Date(
        string='Data Assinatura Acordo',
    )
    tipo_acordo = fields.Selection(
        string='Tipo do Acordo',
        selection=TIPO_ACORDOS,
    )
    competencia_pagamento = fields.Many2one(
        string='Competência de Pagamento',
        comodel_name='account.period',
        help='Competência em que será preciso pagar os '
             'valores reajustados e retroativos',
    )
    data_efetivacao = fields.Date(
        string='Data da Efetivação Retroativa',
    )
    descricao = fields.Char(
        string=u'Descrição',
    )
    remuneracao_relativa_sucessao = fields.Selection(
        string='Remuneração relativa a sucessão',
        selection=[
            ('S', 'Sim'),
            ('N', u'Não'),
        ],
        help='Indicar se a remuneração é relativa a verbas de natureza salarial '
             'ou não salarial devidas pela empresa sucessora a empregados '
             'desligados ainda na sucedida',
    )
    valor_reajuste_salarial = fields.Float(
        string='Valor Reajuste(%)',
    )
    diferenca_salarial_id = fields.Many2one(
        string=u'Rúbrica Diferença Salarial',
        comodel_name='hr.salary.rule',
    )
    diferenca_ferias_id = fields.Many2one(
        string=u'Rúbrica Diferença Férias',
        comodel_name='hr.salary.rule',
    )

    periodo_ids = fields.One2many(
        string='Periodos',
        comodel_name='account.period',
        inverse_name='acordo_coletivo_id',
    )

    diferenca_periodo_ids = fields.One2many(
        string=u'Diferenças nos períodos',
        comodel_name='l10n.br.hr.acordo.coletivo.line',
        inverse_name='acordo_coletivo_id'
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = 'Acordo Coletivo - {}'.format(
                record.competencia_pagamento.code or '--/----')

    @api.multi
    def _get_periodos_retroativos(self):
        for record in self:
            periodos = self.env['account.period'].search(
                [
                    ('date_start', '>=', record.data_efetivacao),
                    ('date_stop', '<', record.competencia_pagamento.date_stop),
                    ('special', '=', False),
                ]
            )

            record.periodo_ids = [(6, 0, periodos.ids)]

    @api.multi
    def _get_diferencas_retroativas(self):
        for record in self:

            if not record.periodo_ids:
                record._get_diferencas_retroativas()

            record.diferenca_periodo_ids.unlink()

            contract_ids = self.env['hr.contract'].search(
                [('date_end', '=', False)])

            for contrato in contract_ids:
                for periodo in record.periodo_ids:
                    payslip_ids = self.env['hr.payslip'].search(
                        [('date_from', '>=', periodo.date_start),
                         ('date_from', '<=', periodo.date_stop),
                         ('tipo_de_folha', 'in', ['normal', 'ferias']),
                         ('contract_id', '=', contrato.id)]
                    )

                    for payslip in payslip_ids:
                        vals = {}
                        valor_bruto = payslip.mapped('line_ids').filtered(
                            lambda l: l.salary_rule_id.code == 'BRUTO'
                        ).total
                        valor_diferenca = (valor_bruto * (1 + (record.valor_reajuste_salarial/100))) - valor_bruto
                        vals = {
                            'contract_id': contrato.id,
                            'holerite_id': payslip.id,
                            'period_id': periodo.id,
                            'valor': valor_diferenca,
                            'acordo_coletivo_id': record.id,
                        }

                        if payslip.tipo_de_folha == 'normal':
                            vals['rubrica_diferenca_id'] = record.diferenca_salarial_id.id
                        else:
                            vals['rubrica_diferenca_id'] = record.diferenca_ferias_id.id

                        self.env['l10n.br.hr.acordo.coletivo.line'].create(vals)

    @api.multi
    def buscar_periodos_retroativos(self):
        for record in self:
            record._get_periodos_retroativos()

    @api.multi
    def gerar_diferencas_retroativos(self):
        for record in self:
            record._get_diferencas_retroativas()


class L10nBrHrAcordoColetivoLine(models.Model):
    _name = 'l10n.br.hr.acordo.coletivo.line'

    contract_id = fields.Many2one(
        string='Contrato',
        comodel_name='hr.contract',
    )
    holerite_id = fields.Many2one(
        string='Holerite',
        comodel_name='hr.payslip',
    )
    period_id = fields.Many2one(
        string='Periodo',
        comodel_name='account.period',
    )
    rubrica_diferenca_id = fields.Many2one(
        string='Rúbrica',
        comodel_name='hr.salary.rule',
    )
    valor = fields.Float(
        string='Valor',
    )
    acordo_coletivo_id = fields.Many2one(
        string='Acordo Coletivo',
        comodel_name='l10n.br.hr.acordo.coletivo',
    )
