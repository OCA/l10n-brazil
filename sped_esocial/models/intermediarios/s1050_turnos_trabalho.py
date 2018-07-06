# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pysped
from openerp import api, models, fields
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedEsocialTurnosTrabalho(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.turnos.trabalho"

    name = fields.Char(
        related='sped_esocial_turnos_trabalho_id.name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
        required=True,
    )
    sped_esocial_turnos_trabalho_id = fields.Many2one(
        string="Turno de Trabalho",
        comodel_name="esocial.turnos.trabalho",
        required=True,
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
        for turno in self:
            situacao_esocial = '0'  # Inativa

            # Se a empresa possui um registro de inclusão confirmado e
            # não precisa atualizar nem excluir então ela está Ativa
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao == '4':
                if not turno.precisa_atualizar and not \
                        turno.precisa_excluir:
                    situacao_esocial = '1'
                else:
                    situacao_esocial = '2'

                # Se já possui um registro de exclusão confirmado, então
                # é situação é Finalizada
                if turno.sped_exclusao and \
                        turno.sped_exclusao.situacao == '4':
                    situacao_esocial = '9'

            # Se a empresa possui algum registro que esteja em fase de
            # transmissão então a situação é Aguardando Transmissão
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao != '4':
                situacao_esocial = '3'
            if turno.sped_exclusao and \
                    turno.sped_exclusao.situacao != '4':
                situacao_esocial = '3'
            for alteracao in turno.sped_alteracao:
                if alteracao.situacao != '4':
                    situacao_esocial = '3'

            # Popula na tabela
            turno.situacao_esocial = situacao_esocial

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_precisa_enviar(self):

        # Roda todos os registros da lista
        for turno in self:

            # Inicia as variáveis como False
            precisa_incluir = False
            precisa_atualizar = False
            precisa_excluir = False

            # Se a empresa matriz tem um período inicial definido e não
            # tem um registro S1000 de inclusão # confirmado,
            # então precisa incluir
            if turno.company_id.esocial_periodo_inicial_id:
                if not turno.sped_inclusao or \
                        turno.sped_inclusao.situacao != '4':
                    precisa_incluir = True

            # Se a empresa já tem um registro de inclusão confirmado mas a
            # data da última atualização é menor que a o write_date da empresa,
            # então precisa atualizar
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao == '4':
                if turno.ultima_atualizacao < \
                        turno.company_id.write_date:
                    precisa_atualizar = True

            # Se a empresa já tem um registro de inclusão confirmado, tem um
            # período final definido e não tem um
            # registro de exclusão confirmado, então precisa excluir
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao == '4':
                if turno.company_id.esocial_periodo_final_id:
                    if not turno.sped_exclusao or \
                            turno.sped_exclusao != '4':
                        precisa_excluir = True

            # Popula os campos na tabela
            turno.precisa_incluir = precisa_incluir
            turno.precisa_atualizar = precisa_atualizar
            turno.precisa_excluir = precisa_excluir

    @api.depends('sped_inclusao',
                 'sped_alteracao', 'sped_alteracao.situacao',
                 'sped_exclusao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for turno in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if turno.sped_inclusao and \
                    turno.sped_inclusao.situacao == '4':
                ultima_atualizacao = turno.sped_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de
            # origem da última alteração
            for alteracao in turno.sped_alteracao:
                if alteracao.situacao == '4':
                    if alteracao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = alteracao.data_hora_origem

            # Se tiver exclusão, pega a data/hora de origem da exclusão
            if turno.sped_exclusao and \
                    turno.sped_exclusao.situacao == '4':
                ultima_atualizacao = turno.sped_exclusao.data_hora_origem

            # Popula o campo na tabela
            turno.ultima_atualizacao = ultima_atualizacao

    @api.multi
    def gerar_registro(self):
        if self.precisa_incluir or self.precisa_atualizar or \
                self.precisa_excluir:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1050',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'evento': 'evtTabHorTur',
                'origem': (
                        'esocial.turnos.trabalho,%s' %
                        self.sped_esocial_turnos_trabalho_id.id),
                'origem_intermediario': (
                        'sped.esocial.turnos.trabalho,%s' % self.id),
            }
            if self.precisa_incluir:
                values['operacao'] = 'I'
                sped_inclusao = self.env['sped.registro'].create(values)
                self.sped_inclusao = sped_inclusao
            elif self.precisa_atualizar:
                values['operacao'] = 'A'
                sped_alteracao = self.env['sped.registro'].create(values)
                self.sped_inclusao = sped_alteracao
            elif self.precisa_excluir:
                values['operacao'] = 'E'
                sped_exclusao = self.env['sped.registro'].create(values)
                self.sped_exclusao = sped_exclusao

    @api.multi
    def popula_xml(self):
        S1050 = pysped.esocial.leiaute.S1050_2()

        # Popula ideEvento
        S1050.tpInsc = '1'
        S1050.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]
        S1050.evento.ideEvento.tpAmb.valor = int(self.ambiente)
        # Processo de Emissão = Aplicativo do Contribuinte
        S1050.evento.ideEvento.procEmi.valor = '1'
        S1050.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1050.evento.ideEmpregador.tpInsc.valor = '1'
        S1050.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula ideHorContratual
        S1050.evento.infoHorContratual.operacao = 'I'
        S1050.evento.infoHorContratual.ideHorContratual.codHorContrat.valor = \
            self.origem.sped_esocial_turnos_trabalho_id.cod_hor_contrat
        # S1050.evento.infoHorContratual.ideHorContratual.iniValid.valor =
        # self.origem.sped_esocial_turnos_trabalho_id.ini_valid
        S1050.evento.infoHorContratual.ideHorContratual.iniValid.valor = \
            self.origem.sped_esocial_turnos_trabalho_id.ini_valid.code[3:7] + \
            '-' + \
            self.origem.sped_esocial_turnos_trabalho_id.ini_valid.code[0:2]
        if self.origem.sped_esocial_turnos_trabalho_id.fim_valid:
            # S1050.evento.infoHorContratual.ideHorContratual.fimValid.valor =
            # self.origem.sped_esocial_turnos_trabalho_id.fim_valid
            S1050.evento.infoHorContratual.ideHorContratual.fimValid.valor = \
                self.origem.sped_esocial_turnos_trabalho_id.fim_valid.code[3:7]\
                + '-' + \
                self.origem.sped_esocial_turnos_trabalho_id.fim_valid.code[0:2]

        # Popula dadosHorContratual
        S1050.evento.infoHorContratual.dadosHorContratual.hrEntr.valor = \
            self.origem.sped_esocial_turnos_trabalho_id.hr_entr.replace(
                ":", "")
        S1050.evento.infoHorContratual.dadosHorContratual.hrSaida.valor = \
            self.origem.sped_esocial_turnos_trabalho_id.hr_saida.replace(
                ":", "")
        S1050.evento.infoHorContratual.dadosHorContratual.durJornada.valor = \
            self.origem.sped_esocial_turnos_trabalho_id.dur_jornada
        S1050.evento.infoHorContratual.dadosHorContratual.perHorFlexivel.valor \
            = self.origem.sped_esocial_turnos_trabalho_id.per_hor_flexivel

        for intervalo in self.origem.sped_esocial_turnos_trabalho_id.\
                horario_intervalo_ids:
            sped_intervalo = pysped.esocial.leiaute.HorarioIntervalo_2()
            sped_intervalo.tpInterv.valor = intervalo.tp_interv
            sped_intervalo.durInterv.valor = intervalo.dur_interv
            sped_intervalo.iniInterv.valor = intervalo.ini_interv.replace(
                ":", "")
            sped_intervalo.termInterv.valor = intervalo.term_interv.replace(
                ":", "")

            S1050.evento.infoHorContratual.dadosHorContratual. \
                horarioIntervalo.append(sped_intervalo)
        # Gera
        dh_transmissao = datetime.now().strftime('%Y%m%d%H%M%S')
        S1050.gera_id_evento(dh_transmissao)

        return S1050

    @api.multi
    def retorno_sucesso(self):
        pass
