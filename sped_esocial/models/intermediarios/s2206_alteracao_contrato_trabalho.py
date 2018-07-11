# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedAlteracaoContrato(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.alteracao.contrato"
    _rec_name = "hr_contract_id"
    _order = "company_id"

    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_contract_id = fields.Many2one(
        string='Contrato de Trabalho',
        comodel_name='hr.contract',
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
        for contrato in self:
            situacao_esocial = '1'

            for alteracao in contrato.sped_alteracao:
                situacao_esocial = alteracao.situacao

            # Popula na tabela
            contrato.situacao_esocial = situacao_esocial

    @api.depends('sped_alteracao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for contrato in self:

            # Inicia as variáveis como False
            precisa_atualizar = False

            # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
            if self.situacao_esocial != '3':

                # Se a empresa já tem um registro de inclusão confirmado mas
                # a data da última atualização é menor que a o write_date da
                # empresa, então precisa atualizar
                if not self.precisa_atualizar or contrato.ultima_atualizacao \
                        < contrato.hr_contract_id.write_date:
                    precisa_atualizar = True

            # Popula os campos na tabela
            contrato.precisa_atualizar = precisa_atualizar

    @api.depends('sped_alteracao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for contrato in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver alterações pega a data/hora de origem da última alteração
            for alteracao in contrato.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Popula o campo na tabela
            contrato.ultima_atualizacao = ultima_atualizacao

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2205 de alteração, se for necessário
        if self.precisa_atualizar:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2206',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'A',
                'evento': 'evtAltContratual',
                'origem': ('hr.contract,%s' % self.hr_contract_id.id),
                'origem_intermediario': (
                        'sped.esocial.alteracao.contrato,%s' % self.id),
            }

            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_alteracao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente a alteração de
        dados contratuais
        """
        # # Cria o registro
        # S2205 = pysped.esocial.leiaute.S2205_2()
        # empregado_id = self.hr_contract_id
        #
        # # Popula ideEvento
        # S2205.tpInsc = '1'
        # S2205.nrInsc = limpa_formatacao(
        #     empregado_id.company_id.cnpj_cpf
        # )[0:8]
        # S2205.evento.ideEvento.indRetif.valor = '1'
        # S2205.evento.ideEvento.tpAmb.valor = int(
        #     empregado_id.company_id.esocial_tpAmb
        # )
        #
        # # Popula ideEmpregador (Dados do Empregador)
        # S2205.evento.ideEmpregador.tpInsc.valor = '1'
        # S2205.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
        #     empregado_id.company_id.cnpj_cpf)[0:8]

        return

    @api.multi
    def retorno_sucesso(self):
        self.ensure_one()
