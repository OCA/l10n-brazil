# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
import pysped


class SpedHrRescisaoAutonomo(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.rescisao.autonomo"

    name = fields.Char(
        string='name',
        compute='_compute_display_name'
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    sped_hr_rescisao_id = fields.Many2one(
        string="Rescisão Trabalhista",
        comodel_name="hr.payslip",
        required=True,
    )
    sped_s2399_registro_inclusao = fields.Many2one(
        string='Registro S-2399',
        comodel_name='sped.registro',
    )
    sped_s2399_registro_retificacao = fields.Many2many(
        string='Registro S-2399 - Retificação',
        comodel_name='sped.registro',
    )
    situacao_s2399 = fields.Selection(
        string='Situação no e-Social',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        compute="compute_situacao_esocial",
        readonly=True,
    )
    ultima_atualizacao = fields.Datetime(
        string='Data da última atualização',
        compute='compute_ultima_atualizacao',
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
        help='e-Social: S2399 - pensAlim'
    )
    perc_aliment = fields.Float(
        string='Percentual da Pensão',
        help='e-Social: S2399 - percAliment',
    )
    vr_alim = fields.Float(
        string='Valor da Pensão',
        help='e-Social: S2399 - vrAlim'
    )

    @api.depends('sped_s2399_registro_inclusao',
                 'sped_s2399_registro_retificacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for desligamento in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if desligamento.sped_s2399_registro_inclusao and \
                    desligamento.sped_s2399_registro_inclusao.situacao == '4':
                ultima_atualizacao = \
                    desligamento.sped_s2399_registro_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for retificacao in desligamento.sped_s2399_registro_retificacao:
                if retificacao.situacao == '4':
                    if retificacao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = retificacao.data_hora_origem

            # Popula o campo na tabela
            desligamento.ultima_atualizacao = ultima_atualizacao

    @api.depends('sped_s2399_registro_inclusao',
                 'sped_s2399_registro_retificacao')
    def compute_situacao_esocial(self):
        for desligamento in self:
            situacao_esocial = '1'

            if desligamento.sped_s2399_registro_inclusao:
                situacao_esocial = \
                    desligamento.sped_s2399_registro_inclusao.situacao

            for retificao in desligamento.sped_s2399_registro_retificacao:
                situacao_esocial = retificao.situacao

            # Popula na tabela
            desligamento.situacao_esocial = situacao_esocial

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2399 - Desligamento {}'.format(record.id)

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao desligamento de
        um contrato de trabalho
        :return:
        """
        # Cria o registro
        S2399 = pysped.esocial.leiaute.S2399_2()

        #
        S2399.tpInsc = '1'
        S2399.nrInsc = limpa_formatacao(
            self.sped_hr_rescisao_id.company_id.cnpj_cpf)[0:8]
        S2399.evento.ideEvento.tpAmb.valor = int(
            self.sped_hr_rescisao_id.company_id.esocial_tpAmb)
        # Processo de Emissão = Aplicativo do Contribuinte
        S2399.evento.ideEvento.procEmi.valor = '1'
        S2399.evento.ideEvento.verProc.valor = '8.0'  # Odoo v8.0

        # Popula ideEmpregador (Dados do Empregador)
        S2399.evento.ideEmpregador.tpInsc.valor = '1'
        S2399.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            self.sped_hr_rescisao_id.company_id.cnpj_cpf)[0:8]

        # evtTSVTermino.ideTrabSemVinculo
        employee_id = self.sped_hr_rescisao_id.contract_id.employee_id
        S2399.evento.ideTrabSemVinculo.cpfTrab.valor = \
            limpa_formatacao(employee_id.cpf)
        S2399.evento.ideTrabSemVinculo.nisTrab.valor = \
            limpa_formatacao(employee_id.pis_pasep)
        S2399.evento.ideTrabSemVinculo.codCateg.valor = \
            self.sped_hr_rescisao_id.contract_id.categoria

        # evtTSVTermino.infoTSVTermino
        rescisao_id = self.sped_hr_rescisao_id
        S2399.evento.infoTSVTermino.dtTerm.valor = fields.Datetime.now()
        if rescisao_id.contract_id.categoria in ['721','722']:
            S2399.evento.infoTSVTermino.mtvDesligTSV.valor = \
                rescisao_id.mtv_deslig.codigo

        # evtTSVTermino.infoTSVTermino.VerbasResc
        verba_rescisoria = pysped.esocial.leiaute.S2399_VerbasResc_2()

        # evtTSVTermino.infoTSVTermino.VerbasResc.DmDev
        dm_dev = pysped.esocial.leiaute.S2399_DmDev_2()
        dm_dev.ideDmDev.valor = self.sped_hr_rescisao_id.number

        # evtTSVTermino.infoTSVTermino.VerbasResc.DmDev.ideEstabLot
        ide_estab_lot = pysped.esocial.leiaute.S2399_IdeEstabLot_2()
        ide_estab_lot.tpInsc.valor = '1'
        ide_estab_lot.nrInsc.valor = \
            limpa_formatacao(rescisao_id.company_id.cnpj_cpf)
        ide_estab_lot.codLotacao.valor = \
            rescisao_id.company_id.cod_lotacao

        # Verbas rescisórias do trabalhador
        for rubrica_line in rescisao_id.line_ids:
            if rubrica_line.salary_rule_id.category_id.id in (
                    self.env.ref('hr_payroll.PROVENTO').id,
                    self.env.ref('hr_payroll.DEDUCAO').id
            ):
                if rubrica_line.salary_rule_id.code != 'PENSAO_ALIMENTICIA':
                    if rubrica_line.total > 0:

                        det_verbas = pysped.esocial.leiaute.S2399_DetVerbas_2()
                        det_verbas.codRubr.valor = \
                            rubrica_line.salary_rule_id.codigo
                        det_verbas.ideTabRubr.valor = \
                            rubrica_line.salary_rule_id.identificador
                        # det_verbas.qtdRubr.valor = ''
                        # det_verbas.fatorRubr.valor = ''
                        # det_verbas.vrunit.valor = ''
                        det_verbas.vrRubr.valor = str(rubrica_line.total)
                        ide_estab_lot.detVerbas.append(det_verbas)

        # evtTSVAltContr.infoTSVTermino.VerbasResc.DmDev.ideEstabLot.InfoAgNocivo
        if rescisao_id.contract_id.categoria in ['738','731','734']:
            info_ag_nocivo = pysped.esocial.leiaute.S2399_InfoAgNocivo_2()
            info_ag_nocivo.grauExp.valor = 1
            ide_estab_lot.infoAgNocivo.append(info_ag_nocivo)

        # relacionando as classes
        dm_dev.ideEstabLot.append(ide_estab_lot)
        verba_rescisoria.dmDev.append(dm_dev)
        S2399.evento.infoTSVTermino.verbasResc.append(verba_rescisoria)

        return S2399

    @api.multi
    def retorno_sucesso(self):
        pass
