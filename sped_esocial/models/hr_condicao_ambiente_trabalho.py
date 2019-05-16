# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class HrCondicaoAmbienteTrabalho(models.Model):
    _name = 'hr.condicao.ambiente.trabalho'
    _description = u'Condições Ambientais de Trabalho - Fator de Risco'
    _order = 'contract_id'
    _sql_constraints = [
        ('inicio_condicao_contract_id',
         'unique(inicio_condicao, contract_id)',
         'Este contrato já possiu um relatório de '
         'Condições Ambientais de Trabalho com esta data de início!'
         )
    ]

    state = fields.Selection(
        string='Situação',
        selection=[
            ('0', 'Inativo'),
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluído'),
        ],
        default='0',
        compute='_compute_state',
    )
    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
    )
    contract_id = fields.Many2one(
        string=u'Contrato de Trabalho',
        comodel_name='hr.contract',
        domain=[('situacao_esocial', '=', 1)]
    )
    inicio_condicao = fields.Date(
        string=u'Data de início',
    )
    hr_ambiente_ids = fields.Many2many(
        string='Ambientes',
        comodel_name='hr.ambiente.trabalho',
        relation='condicao_ambiente_ambiente_trabalho_rel',
        column1='hr_ambiente_trabalho_id',
        column2='hr_condicao_ambiente_trabalho_id',
    )
    hr_atividade_id = fields.Many2one(
        string='Atividades',
        comodel_name='hr.informativo.atividade.trabalho',
    )
    hr_fator_risco_ids = fields.Many2many(
        string='Fatores de Risco',
        comodel_name='hr.fator.risco',
    )
    hr_responsavel_ambiente_ids = fields.Many2many(
        string=u'Responsáveis de Registros Ambientais',
        comodel_name='hr.responsavel.ambiente',
    )
    metodologia_erg = fields.Text(
        string=u'Metodologia Levantamento Riscos Ergonômicos',
        size=999,
    )
    obs_complementares = fields.Text(
        string=u'Observações Complementares',
        size=999,
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.condicao.ambiente.trabalho',
    )

    @api.multi
    def _compute_name(self):
        for record in self:
            record.name = '{} - {}'.format(
                record.contract_id.nome_contrato, record.inicio_condicao)

    @api.multi
    def _compute_state(self):
        for record in self:
            if not record.sped_intermediario_id:
                record.state = 0
            else:
                record.state = record.sped_intermediario_id.situacao_esocial

    def gerar_intermediario(self):
        if not self.sped_intermediario_id:
            vals = {
                'company_id': self.contract_id.company_id.id if
                self.contract_id.company_id.eh_empresa_base else
                self.contract_id.company_id.matriz.id,
                'hr_condicao_ambiente_trabalho_id': self.id,
            }
            self.sped_intermediario_id = self.env[
                'sped.hr.condicao.ambiente.trabalho'].create(vals)
            self.sped_intermediario_id.gerar_registro()

    @api.multi
    def button_enviar_esocial(self):
        self.gerar_intermediario()

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.contract_id.employee_id

    @api.multi
    def unlink(self):
        for record in self:
            for registro in record.sped_intermediario_id.sped_inclusao:
                if registro.situacao == '4':
                    raise Warning(
                        'Não é possível excluír um registro '
                        'que foi transmitido para o e-Social!'
                    )
            record.sped_intermediario_id.unlink()
            super(HrCondicaoAmbienteTrabalho, record).unlink()
