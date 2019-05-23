# -*- coding: utf-8 -*-
#
# Copyright 2019 ABGF - Luiz Felipe do Divino <luiz.divino@abgf.gov.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from openerp import api, fields, models, _
from openerp.exceptions import Warning

MOD_TREI = [
    ('1', 'Presencial'),
    ('2', 'Educação a Distância (EAD)'),
    ('3', 'Semipresencial'),
]

TIPO_TREI = [
    ('1', 'Inicial'),
    ('2', 'Periódico'),
    ('3', 'Reciclagem'),
    ('4', 'Eventual'),
    ('5', 'Outros'),
]

SIM_NAO = [
    ('S', 'Sim'),
    ('N', 'Não'),
]


class HrTreinamentosCapacitacoes(models.Model):
    _name = 'hr.treinamentos.capacitacoes'
    _description = u'Treinamentos, Capacitações, Exercícios Simulados e ' \
                   u'Outras Anotações'

    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
    )
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
    contract_id = fields.Many2one(
        string=u'Contrato de Trabalho',
        comodel_name='hr.contract',
        domain=[('situacao_esocial', '=', 1)]
    )
    cod_treinamento_cap_id = fields.Many2one(
        string=u'Código do Treinamento',
        comodel_name='sped.treinamentos_capacitacoes'
    )
    obs = fields.Text(
        string=u'Observação',
        size=999,
        help=u'Nome Layout: obsTreiCap - Tamanho: Até 999 Caracteres - '
             u'Observação referente ao '
             u'treinamento/capacitação/exercício simulado.',
    )
    codigo_treinamento = fields.Char(
        string=u'Cod treinamento',
    )
    data_treinamento = fields.Date(
        string=u'Data',
        help=u'Nome Layout: dtTreiCap - Informar a data de início do '
             u'treinamento/capacitação/exercício simulado ou a data '
             u'de início da obrigatoriedade deste evento para o '
             u'empregador no eSocial, a que for mais recente. '
             u'Validação: Deve ser uma data válida, igual ou anterior à '
             u'data atual e igual ou posterior à data de admissão do '
             u'vínculo a que se refere. Não pode ser anterior à data'
             u' de início da obrigatoriedade deste evento para o '
             u'empregador no eSocial.',
    )
    duracao = fields.Integer(
        string=u'Duração em Horas',
        size=6,
        help=u'Nome Layout: durTreiCap - Tamanho: Até 6 Caracteres - '
             u'Informar a duração do treinamento/capacitação/exercício'
             u' simulado, em horas.',
    )
    modalidade = fields.Selection(
        string=u'Modelidade',
        selection=MOD_TREI,
        help=u'Nome Layout: modTreiCap - Tamanho: Até 1 Caracteres - '
             u'Modalidade do treinamento/capacitação/exercício simulado, '
             u'conforme opções abaixo',
    )
    tipo = fields.Selection(
        string=u'Tipo',
        selection=TIPO_TREI,
        help=u'Nome Layout: tpTreiCap - Tamanho: Até 1 Caracteres - Tipo de '
             u'treinamento/capacitação/exercício simulado, '
             u'conforme opções abaixo',
    )
    treinamento_antes_admissao = fields.Selection(
        string=u'Treinamento antes da Admissão',
        selection=SIM_NAO,
        help=u'Nome Layout: indTreinAnt - Tamanho: Até 1 Caracteres - Indicar'
             u' se o treinamento ocorreu antes da admissão, '
             u'em outro empregador',
    )
    treinamento_antes_admissao = fields.Selection(
        string=u'Treinamento antes da Admissão',
        selection=SIM_NAO,
    )
    treinamento_antes_admissao = fields.Selection(
        string=u'Treinamento antes da Admissão',
        selection=SIM_NAO,
    )
    professor_ids = fields.Many2many(
        string=u'Professor Treinamento/Capitação',
        comodel_name='hr.professor.treinamento',
    )
    sped_intermediario_id = fields.Many2one(
        string='Intermediário do e-Social',
        comodel_name='sped.hr.treinamentos.capacitacoes',
    )
    @api.model
    def _compute_name(self):
        for record in self:
            record.name = 'Treinamento: {} - {}'.format(
                record.cod_treinamento_cap_id.codigo,
                record.contract_id.name
            )

    @api.onchange('cod_treinamento_cap_id')
    def _onchange_cod_treinamento_cap(self):
        for record in self:
            if record.cod_treinamento_cap_id:
                record.codigo_treinamento = record.cod_treinamento_cap_id.codigo

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
                'hr_treinamento_capacitacao_id': self.id,
            }
            self.sped_intermediario_id = self.env[
                'sped.hr.treinamentos.capacitacoes'].create(vals)
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
            super(HrTreinamentosCapacitacoes, record).unlink()
