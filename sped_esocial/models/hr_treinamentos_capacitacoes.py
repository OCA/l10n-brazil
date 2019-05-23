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


class HrTreinamentosCapacitacoes(models.Model):
    _name = 'hr.treinamentos.capacitacoes'
    _description = u'Treinamentos, Capacitações, Exercícios Simulados e ' \
                   u'Outras Anotações'

    name = fields.Char(
        string=u'Nome Condição',
        compute='_compute_name',
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
    )
    info_complementares = fields.Boolean(
        string=u'Preencher Informações Complementares',
    )
    data_treinamento = fields.Date(
        string=u'Data',
    )
    duracao = fields.Integer(
        string=u'Duração em Horas',
        size=6,
    )
    modalidade = fields.Selection(
        string=u'Modelidade',
        selection=MOD_TREI,
    )
    tipo = fields.Selection(
        string=u'Tipo',
        selection=TIPO_TREI,
    )
    professor_ids = fields.Many2many(
        string=u'Professor Treinamento/Capitação',
        comodel_name='hr.professor.treinamento',
    )

    @api.model
    def _compute_name(self):
        for record in self:
            record.name = 'Treinamento: {} - {}'.format(
                record.cod_treinamento_cap_id.codigo,
                record.contract_id.name
            )

