# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedEmpregador(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.alteracao.funcionario"
    _rec_name = "company_id"
    _order = "company_id"

    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_employee_id = fields.Many2one(
        string='Funcionário',
        comodel_name='hr.employee',
        required=True,
    )
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Precisa Atualizar'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('sped_alteracao')
    def compute_situacao_esocial(self):
        for empregado in self:
            situacao_esocial = '1'

            for alteracao in empregado.sped_alteracao:
                situacao_esocial = alteracao.situacao

            # Popula na tabela
            empregado.situacao_esocial = situacao_esocial

    @api.depends('sped_alteracao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for empregado in self:

            # Inicia as variáveis como False
            precisa_atualizar = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if self.situacao_esocial != '3':

                # Se a empresa já tem um registro de inclusão confirmado mas
                # a data da última atualização é menor que a o write_date da
                # empresa, então precisa atualizar
                if not self.precisa_atualizar or empregado.ultima_atualizacao < empregado.hr_employee_id.write_date:
                    precisa_atualizar = True

            # Popula os campos na tabela
            empregado.precisa_atualizar = precisa_atualizar

    @api.depends('sped_alteracao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for empregado in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver alterações pega a data/hora de origem da última alteração
            for alteracao in empregado.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Popula o campo na tabela
            empregado.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2205 de alteração, se for necessário
        if self.precisa_atualizar:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2205',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'A',
                'evento': 'evtAltCadastral',
                'origem': ('hr.employee,%s' % self.hr_employee_id.id),
                'origem_intermediario': (
                        'sped.esocial.alteracao.funcionario,%s' % self.id),
            }

            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_alteracao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        pass

    @api.multi
    def retorno_sucesso(self):
        self.ensure_one()
