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

    esocial_id = fields.Many2one(
        string="e-Social",
        comodel_name="sped.esocial",
        required=True,
    )
    sped_esocial_turnos_trabalho_id = fields.Many2one(
        string="Turno de Trabalho",
        comodel_name="esocial.turnos.trabalho",
        required=True,
    )
    sped_s1050_registro = fields.Many2one(
        string='Registro S-1050',
        comodel_name='sped.registro',
    )
    situacao_s1050 = fields.Selection(
        string="Situação S-1050",
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related="sped_s1050_registro.situacao",
        readonly=True,
    )

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