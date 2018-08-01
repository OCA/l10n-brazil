# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor

from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario


class SpedAlteracaoContratoAutonomo(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.alteracao.contrato.autonomo"
    _rec_name = "name"
    _order = "company_id"

    name = fields.Char(
        string='name',
        compute='_compute_display_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_contract_id = fields.Many2one(
        string='Contrato de Trabalho',
        comodel_name='hr.contract',
        required=True,
    )
    # S2306
    sped_alteracao = fields.Many2many(
        string='Alterações',
        comodel_name='sped.registro',
        relation='alteracao_contrato_sem_vinculo_sped_registro_rel',
        column1='sped_esocial_alteracao_contrato_autonomo_id',
        column2='sped_registro_id',
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
        related='hr_contract_id.precisa_atualizar',
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
    )

    @api.depends('hr_contract_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2306 - Alteração de Contratos Sem vínculos {}'.format(
                record.hr_contract_id.display_name or '')

    @api.depends('sped_alteracao')
    def compute_situacao_esocial(self):
        for contrato in self:
            situacao_esocial = '1'

            for alteracao in contrato.sped_alteracao:
                situacao_esocial = alteracao.situacao

            # Popula na tabela
            contrato.situacao_esocial = situacao_esocial

    # @api.multi
    # @api.depends('sped_alteracao')
    # def compute_precisa_enviar(self):
    #
    #     # Roda todos os registros da lista
    #     for contrato in self:
    #
    #         # Inicia as variáveis como False
    #         precisa_atualizar = False
    #
    #         # Se a situação for '3' (Aguardando Transmissão) fica tudo falso
    #         if contrato.situacao_esocial != '3':
    #
    #             # Se a empresa já tem um registro de inclusão confirmado mas
    #             # a data da última atualização é menor que a o write_date da
    #             # empresa, então precisa atualizar
    #             if not contrato.precisa_atualizar or contrato.ultima_atualizacao \
    #                     < contrato.hr_contract_id.write_date:
    #                 precisa_atualizar = True
    #
    #         # Popula os campos na tabela
    #         contrato.precisa_atualizar = precisa_atualizar


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

    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2306 de alteração, se for necessário
        if self.precisa_atualizar:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2306',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'A',
                'evento': 'evtTSVAltContr',
                'origem': ('hr.contract,%s' % self.hr_contract_id.id),
                'origem_intermediario': (
                        'sped.esocial.alteracao.contrato.autonomo,%s' % self.id),
            }

            sped_alteracao = self.env['sped.registro'].create(values)
            self.sped_alteracao = [(4, sped_alteracao.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente a alteração de
        dados contratuais
        """
        # Cria o registro
        S2306 = pysped.esocial.leiaute.S2306_2()
        contrato_id = self.hr_contract_id

        # Campos de controle para gerar ID do Evento -
        S2306.tpInsc = '1'
        S2306.nrInsc = limpa_formatacao(contrato_id.company_id.cnpj_cpf)[0:8]

        # evtTSVAltContr.ideEvento
        S2306.evento.ideEvento.indRetif.valor = '1'
        S2306.evento.ideEvento.procEmi.valor = '1'
        S2306.evento.ideEvento.verProc.valor = '8.0'
        S2306.evento.ideEvento.tpAmb.valor = int(
            contrato_id.company_id.esocial_tpAmb)

        # evtTSVAltContr.ideEvento.ideEmpregador
        S2306.evento.ideEmpregador.tpInsc.valor = '1'
        S2306.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            contrato_id.company_id.cnpj_cpf)[0:8]

        # Popula ideTrabSemVinculo (Identificador do Trabalhador sem Vínculo)
        S2306.evento.ideTrabSemVinculo.cpfTrab.valor = \
            limpa_formatacao(self.hr_contract_id.employee_id.cpf)
        S2306.evento.ideTrabSemVinculo.nisTrab.valor = \
            limpa_formatacao(self.hr_contract_id.employee_id.pis_pasep)
        S2306.evento.ideTrabSemVinculo.codCateg.valor = \
            self.hr_contract_id.categoria

        # evtTSVAltContr.infoTSVAlteracao
        S2306.evento.infoTSVAlteracao.dtAlteracao.valor = fields.Datetime.now()
        S2306.evento.infoTSVAlteracao.natAtividade.valor = \
            contrato_id.nat_atividade or 1

        # infoTSVAlteracao.InfoComplementares.CargoFuncao
        CargoFuncao = pysped.esocial.leiaute.S2306_CargoFuncao_2()

        CargoFuncao.codCargo.valor = self.hr_contract_id.job_id.codigo
        # CargoFuncao.codFuncao.valor = ''

        S2306.evento.infoTSVAlteracao.infoComplementares.cargoFuncao.append(CargoFuncao)


        # infoTSVAlteracao.InfoComplementares.Remuneracao
        Remuneracao = pysped.esocial.leiaute.S2306_Remuneracao_2()

        Remuneracao.vrSalFx.valor = formata_valor(self.hr_contract_id.wage)
        if self.hr_contract_id.salary_unit.code in [7]:
            Remuneracao.vrSalFx.valor = 0
        Remuneracao.undSalFixo.valor = self.hr_contract_id.salary_unit.code
        if self.hr_contract_id.salary_unit.code in [6, 7]:
            Remuneracao.dscSalVar.valor = self.hr_contract_id.dsc_sal_var

        S2306.evento.infoTSVAlteracao.infoComplementares.remuneracao.append(Remuneracao)

        return S2306

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
        pass

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.hr_contract_id.employee_id

    @api.multi
    def transmitir(self):
        self.ensure_one()

        if self.situacao_esocial in ['1', '3']:
            # Identifica qual registro precisa transmitir
            registro = False
            if self.sped_alteracao.situacao in ['1', '3']:
                registro = self.sped_alteracao

            # Com o registro identificado, é só rodar o método
            # transmitir_lote() do registro
            if registro:
                registro.transmitir_lote()

    @api.multi
    def consultar(self):
        self.ensure_one()

        if self.situacao_esocial in ['2']:
            # Identifica qual registro precisa consultar
            registro = False
            if self.sped_alteracao.situacao == '2':
                registro = self.sped_alteracao

            # Com o registro identificado, é só rodar o método consulta_lote() do registro
            if registro:
                registro.consulta_lote()
