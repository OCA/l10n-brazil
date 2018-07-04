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
        compute='_compute_display_name'
    )
    sped_hr_rescisao_id = fields.Many2one(
        string="Rescisão Trabalhista",
        comodel_name="hr.payslip",
        required=True,
    )
    sped_s2200_registro = fields.Many2one(
        string='Registro S-1050',
        comodel_name='sped.registro',
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
    pagamento_pensao = fields.Boolean(
        string='Funcionário paga pensão?',
    )
    pens_alim = fields.Selection(
        string='Pensão Alimentícia',
        selection=[
            ('0', 'Não existe Pensão'),
            ('1', 'Percentual de Pensão'),
            ('2', 'Valor de Pensão'),
            ('3', 'Percentual e Valor de Pensão'),
        ],
        required=True,
        help='e-Social: S2299 - pensAlim'
    )
    perc_aliment = fields.Float(
        string='Percentual da Pensão',
        help='e-Social: S2299 - percAliment',
    )
    vr_alim = fields.Float(
        string='Valor da Pensão',
        help='e-Social: S2299 - vrAlim'
    )

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2299 - Desligamento {}'.format(record.id)

    @api.multi
    def popula_xml(self):
        """
        Função para popular o xml com os dados referente ao desligamento de
        um contrato de trabalho
        :return:
        """
        # Cria o registro
        S2299 = pysped.esocial.leiaute.S2299_2()

        # Popula ideEvento
        S2299.tpInsc = '1'
        S2299.nrInsc = limpa_formatacao(
            self.sped_hr_rescisao_id.company_id.cnpj_cpf
        )[0:8]
        S2299.evento.ideEvento.tpAmb.valor = int(
            self.sped_hr_rescisao_id.company_id.esocial_tpAmb
        )
        # Processo de Emissão = Aplicativo do Contribuinte
        S2299.evento.ideEvento.procEmi.valor = '1'
        S2299.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2299.evento.ideEmpregador.tpInsc.valor = '1'
        S2299.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.sped_hr_rescisao_id.company_id.cnpj_cpf)[0:8]

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

        infoDeslig.mtvDeslig.valor = rescisao_id.mtv_deslig.codigo
        infoDeslig.dtDeslig.valor = rescisao_id.date_to
        if rescisao_id.valor_pgto_aviso_previo_indenizado:
            infoDeslig.indPagtoAPI.valor = 'S'
            infoDeslig.dtProjFimAPI.valor = rescisao_id.data_afastamento
        else:
            infoDeslig.indPagtoAPI.valor = 'N'
        if self.pens_alim == '0':
            infoDeslig.pensAlim.valor = self.pens_alim
        else:
            infoDeslig.pensAlim.valor = self.pens_alim
            if self.perc_aliment:
                infoDeslig.percAliment.valor = self.perc_aliment
            if self.vr_alim:
                infoDeslig.vrAlim.valor = self.vr_alim
        if rescisao_id.contract_id.numero_processo:
            infoDeslig.nrProcTrab.valor = \
                rescisao_id.contract_id.numero_processo
        infoDeslig.indCumprParc.valor = '4'
        verba_rescisoria = pysped.esocial.leiaute.S2299_VerbasResc_2()
        for rubrica_line in rescisao_id.line_ids:
            if rubrica_line.salary_rule_id.category_id.id in (
                    self.env.ref('hr_payroll.PROVENTO').id,
                    self.env.ref('hr_payroll.DEDUCAO').id
            ):
                if rubrica_line.salary_rule_id.code != 'PENSAO_ALIMENTICIA':
                    if rubrica_line.total > 0:
                        ide_dm_dev = pysped.esocial.leiaute.S2299_DmDev_2()
                        ide_dm_dev.ideDmDev.valor = str(rubrica_line.id)
                        info_per_apur = \
                            pysped.esocial.leiaute.S2299_InforPerApur_2()

                        ide_estab_lot = \
                            pysped.esocial.leiaute.S2299_IdeEstabLotApur_2()
                        ide_estab_lot.tpInsc.valor = '1'
                        ide_estab_lot.nrInsc.valor = limpa_formatacao(
                            rescisao_id.company_id.cnpj_cpf
                        )[0:8]
                        ide_estab_lot.codLotacao.valor = \
                            rescisao_id.company_id.cod_lotacao

                        det_verbas = pysped.esocial.leiaute.S2299_DetVerbas_2()
                        det_verbas.codRubr.valor = \
                            rubrica_line.salary_rule_id.codigo
                        det_verbas.ideTabRubr.valor = \
                            rubrica_line.salary_rule_id.identificador
                        # det_verbas.qtdRubr.valor = ''
                        # det_verbas.fatorRubr.valor = ''
                        # det_verbas.vrunit.valor = ''
                        det_verbas.vrRubr.valor = str(rubrica_line.total)

                        ide_estab_lot.detVerbas.append(det_verbas)
                        info_per_apur.ideEstabLot.append(ide_estab_lot)

                        ide_dm_dev.infoPerApur.append(info_per_apur)

                        verba_rescisoria.dmDev.append(ide_dm_dev)

        infoDeslig.verbaResc.append(verba_rescisoria)
        return S2299

    @api.multi
    def retorno_sucesso(self):
        pass
