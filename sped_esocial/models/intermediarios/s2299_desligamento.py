# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, models, fields
from .sped_registro_intermediario import SpedRegistroIntermediario

from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
import pysped


class SpedHrRescisao(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.rescisao"

    name = fields.Char(
        string='name',
    )
    esocial_id = fields.Many2one(
        string="e-Social",
        comodel_name="sped.esocial",
        required=True,
    )
    sped_hr_rescisao_id = fields.Many2one(
        string="Rescisão Trabalhista",
        comodel_name="hr.payroll",
        required=True,
    )
    sped_s2200_registro = fields.Many2one(
        string='Registro S-1050',
        comodel_name='sped.transmissao',
    )
    situacao_s2200 = fields.Selection(
        string="Situação S-1050",
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related="sped_s2200_registro.situacao",
        readonly=True,
    )

    def popula_xml(self):
        # Cria o registro
        S2299 = pysped.esocial.leiaute.S2299_2()

        # Popula ideEvento
        S2299.tpInsc = '1'
        S2299.nrInsc = limpa_formatacao(
            self.sped_hr_rescisao_id.company_id.cnpj_cpf
        )[0:8]
        S2299.evento.ideEvento.tpAmb.valor = int(
            self.sped_hr_rescisao_id.company_id.ambiente
        )
        # Processo de Emissão = Aplicativo do Contribuinte
        S2299.evento.ideEvento.procEmi.valor = '1'
        S2299.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2299.evento.ideEmpregador.tpInsc.valor = '1'
        S2299.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.company_id.cnpj_cpf)[0:8]

        # Popula ideVinculo
        employee_id = self.sped_hr_rescisao_id.contract_id.employee_id
        S2299.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            employee_id.cpf
        )
        S2299.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            employee_id.pis_pasep
        )
        S2299.evento.ideVinculo.matricula.valor = \
            self.sped_hr_rescisao_id.contract_id.matricula

        # Popula infoDeslig (Informações relativas ao desligamento do
        # vínculo indicado
        infoDeslig = S2299.evento.infoDeslig
        rescisao_id = self.sped_hr_rescisao_id

        infoDeslig.mtvDeslig.valor = rescisao_id.mtv_deslig
        infoDeslig.dtDeslig.valor = rescisao_id.date_to
        if rescisao_id.valor_pgto_aviso_previo_indenizado:
            infoDeslig.indPagtoAPI.valor = 'S'
            infoDeslig.dtProjFimAPI.valor = rescisao_id.data_afastamento
        else:
            infoDeslig.indPagtoAPI.valor = 'N'
        # if rescisao_id.buscar_pensao_alimenticia():
        #     continue
        if rescisao_id.contract_id.numero_processo:
            infoDeslig.nrProcTrab.valor = \
                rescisao_id.contract_id.numero_processo
        infoDeslig.indCumprParc.valor = '4'
        for rubrica_line in rescisao_id.line_ids:
            pass

        return S2299
