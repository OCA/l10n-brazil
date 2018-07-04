# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from .sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedEmpregador(models.Model, SpedRegistroIntermediario):
    _name = "sped.empregador"

    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    sped_inclusao = fields.Many2one(
        string='Inclusão',
        comodel_name='sped.registro',
    )
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
    )
    sped_exclusao = fields.Many2one(
        string='Exclusão',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )
    precisa_incluir = fields.Boolean(
        string='Precisa incluir dados?',
        compute='compute_precisa_enviar',
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa atualizar dados?',
        compute='compute_precisa_enviar',
    )
    precisa_excluir = fields.Boolean(
        string='Precisa excluir dados?',
        compute='compute_precisa_enviar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('sped_inclusao', 'sped_exclusao')
    def compute_situacao_esocial(self):
        for empregador in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e não precisa atualizar nem excluir
            # então ela está Ativa
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                if not empregador.precisa_atualizar and not empregador.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if empregador.sped_exclusao and empregador.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui um registro de inclusão que esteja em fase de transmissão
            # então a situação é Aguardando Transmissão
            elif empregador.sped_inclusao and empregador.sped_inclusao.situacao != '4':
                situacao_esocial = '3'

            # Popula na tabela
            empregador.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao',
                 'company_id.esocial_periodo_inicial_id', 'company_id.esocial_periodo_final_id')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for empregador in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa matriz tem um período inicial definido e não tem um registro S1000 de inclusão
            # confirmado, então precisa incluir
            if empregador.company_id.esocial_periodo_inicial_id:
                if not empregador.sped_inclusao or empregador.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado mas a data da última atualização
            # é menor que a o write_date da empresa, então precisa atualizar
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                if empregador.ultima_atualizacao < empregador.company_id.write_date:
                    precisa_atualizar = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um período final definido e
            # não tem um registro de exclusão confirmado, então precisa excluir
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                if empregador.company_id.esocial_periodo_final_id:
                    if not empregador.sped_exclusao or empregador.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            empregador.precisa_incluir = precisa_incluir
            empregador.precisa_atualizar = precisa_atualizar
            empregador.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for empregador in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if empregador.sped_inclusao and empregador.sped_inclusao.situacao == '4':
                ultima_atualizacao = empregador.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for alteracao in empregador.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if empregador.sped_exclusao and empregador.sped_exclusao.situacao == '4':
                ultima_atualizacao = empregador.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            empregador.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualiza_esocial(self):
        self.ensure_one()

        # Criar o registro S-1000 de inclusão, se for necessário
        if self.precisa_incluir:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1000',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'I',
                'evento': 'evtInfoEmpregador',
                'origem': ('res.company,%s' % self.company_id.id),
                'origem_intermediario': ('sped.empregador,%s' % self.id),
            }

            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_inclusao = sped_inclusao

        # Criar o registro S-1000 de alteração, se for necessário
        if self.precisa_atualizar:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1000',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'A',
                'evento': 'evtInfoEmpregador',
                'origem': ('res.company,%s' % self.comapny_id.id),
                'origem_intermediario': ('sped.empregador,%s' % self.id),
            }

            sped_atualizacao = self.env['sped.registro'].create(values)
            self.sped_atualizacao = [(4, sped_atualizacao.id)]

        # Criar o registro S-1000 de exclusão, se for necessário
        if self.precisa_excluir:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1000',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'E',
                'evento': 'evtInfoEmpregador',
                'origem': ('res.company,%s' % self.company_id.id),
                'origem_intermediario': ('sped.empregador,%s' % self.id),
            }

            sped_exclusao = self.env['sped.registro'].create(values)
            self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self):
        self.ensure_one()

    @api.multi
    def retorno_sucesso(self):
        self.ensure_one()
