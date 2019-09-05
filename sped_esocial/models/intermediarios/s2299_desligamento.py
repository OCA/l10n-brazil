# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
import pysped


class SpedHrRescisao(models.Model, SpedRegistroIntermediario):
    _name = "sped.hr.rescisao"
    _rec_name = 'name'

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
    data_rescisao = fields.Date(
        string="Data de Desligamento",
        related='sped_hr_rescisao_id.data_afastamento',
        store=True,
    )
    sped_s2299_registro_inclusao = fields.Many2one(
        string='Registro S-2299',
        comodel_name='sped.registro',
    )
    sped_s2299_registro_retificacao = fields.Many2many(
        string='Registro S-2299 - Retificação',
        comodel_name='sped.registro',
    )
    situacao_s2299 = fields.Selection(
        string='Situação no e-Social',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
        ],
        compute="compute_situacao_esocial",
        store=True,
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
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    trabalhador_id = fields.Many2one(
        string='Trabalhador',
        comodel_name='hr.employee',
    )
    s5001_id = fields.Many2one(
        string='S-5001 (Contribuições Sociais)',
        comodel_name='sped.contribuicao.inss',
    )

    @api.depends('sped_s2299_registro_inclusao.situacao',
                 'sped_s2299_registro_retificacao.situacao')
    def compute_ultima_atualizacao(self):

        # Roda todos os registros da lista
        for desligamento in self:

            # Inicia a última atualização com a data/hora now()
            ultima_atualizacao = fields.Datetime.now()

            # Se tiver o registro de inclusão, pega a data/hora de origem
            if desligamento.sped_s2299_registro_inclusao and \
                    desligamento.sped_s2299_registro_inclusao.situacao == '4':
                ultima_atualizacao = \
                    desligamento.sped_s2299_registro_inclusao.data_hora_origem

            # Se tiver alterações, pega a data/hora de origem da última alteração
            for retificacao in desligamento.sped_s2299_registro_retificacao:
                if retificacao.situacao == '4':
                    if retificacao.data_hora_origem > ultima_atualizacao:
                        ultima_atualizacao = retificacao.data_hora_origem

            # Popula o campo na tabela
            desligamento.ultima_atualizacao = ultima_atualizacao

    @api.depends('sped_s2299_registro_inclusao.situacao',
                 'sped_s2299_registro_retificacao.situacao')
    def compute_situacao_esocial(self):
        for desligamento in self:
            situacao_esocial = '1'

            if desligamento.sped_s2299_registro_inclusao:
                situacao_esocial = \
                    desligamento.sped_s2299_registro_inclusao.situacao

            for retificao in desligamento.sped_s2299_registro_retificacao:
                situacao_esocial = self.get_registro_para_retificar(retificao[0])

            # Popula na tabela
            desligamento.situacao_s2299 = situacao_esocial

    @api.multi
    def gerar_registro(self):
        values = {
            'tipo': 'esocial',
            'registro': 'S-2299',
            'ambiente': self.company_id.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtDeslig',
            'origem': (
                    'hr.payslip,%s' %
                    self.sped_hr_rescisao_id.id),
            'origem_intermediario': (
                    'sped.hr.rescisao,%s' % self.id),
        }
        if not self.sped_s2299_registro_inclusao:
            # Cria o registro de envio
            sped_inclusao = self.env['sped.registro'].create(values)
            self.sped_s2299_registro_inclusao = sped_inclusao
            return

        # Cria o registro de Retificação
        values['operacao'] = 'R'
        sped_retificacao = self.env['sped.registro'].create(values)
        self.sped_s2299_registro_retificacao = [(4, sped_retificacao.id)]

    @api.multi
    @api.depends('sped_hr_rescisao_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2299 - Desligamento {}'.format(
                record.sped_hr_rescisao_id.contract_id.display_name)

    def get_registro_para_retificar(self, sped_registro):
        """
        Identificar o registro para retificar
        :return:
        """
        # Se tiver registro de retificação com erro ou nao possuir nenhuma
        # retificação ainda, retornar o registro que veio no parametro
        retificacao_com_erro = sped_registro.retificacao_ids.filtered(
            lambda x: x.situacao in ['1', '3'])
        if retificacao_com_erro or not sped_registro.retificacao_ids:
            return sped_registro

        # Do contrario navegar ate as retificacoes com sucesso e efetuar a
        # verificacao de erro novamente
        else:
            registro_com_sucesso = sped_registro.retificacao_ids.filtered(
                lambda x: x.situacao not in ['1', '3'])

            return self.get_registro_para_retificar(registro_com_sucesso[0])

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao desligamento de
        um contrato de trabalho
        :return:
        """
        periodo_id = self.periodo_id.find(self.sped_hr_rescisao_id.data_afastamento)
        convencao_coletiva_id = self.env['l10n.br.hr.acordo.coletivo'].search(
            [('competencia_pagamento', '=', periodo_id.id)])

        periodo_apuracao = periodo_id.code[3:7] + '-' + \
                           periodo_id.code[0:2]

        periodo_apuracao_inverso = periodo_id.code[0:2] + '-' + \
                                   periodo_id.code[3:7]

        # Validação
        validacao = ""

        # Cria o registro
        S2299 = pysped.esocial.leiaute.S2299_2()

        # Popula ideEvento
        S2299.tpInsc = '1'
        S2299.nrInsc = limpa_formatacao(
            self.sped_hr_rescisao_id.sped_s2299.company_id.cnpj_cpf
        )[0:8]
        S2299.evento.ideEvento.tpAmb.valor = int(
            self.sped_hr_rescisao_id.sped_s2299.company_id.esocial_tpAmb
        )

        # Registro Original
        indRetif = '1'

        # Se for uma retificação
        if operacao == 'R':
            indRetif = '2'

            registro_para_retificar = self.get_registro_para_retificar(
                self.sped_s2299_registro_inclusao)

            S2299.evento.ideEvento.nrRecibo.valor = \
                registro_para_retificar.recibo

        S2299.evento.ideEvento.indRetif.valor = indRetif

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

        infoDeslig.mtvDeslig.valor = rescisao_id.mtv_deslig_esocial.codigo
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

        ide_dm_dev = pysped.esocial.leiaute.S2299_DmDev_2()
        ide_dm_dev.ideDmDev.valor = self.sped_hr_rescisao_id.number
        info_per_apur = \
            pysped.esocial.leiaute.S2299_InforPerApur_2()

        ide_estab_lot = \
            pysped.esocial.leiaute.S2299_IdeEstabLotApur_2()
        ide_estab_lot.tpInsc.valor = '1'
        ide_estab_lot.nrInsc.valor = limpa_formatacao(
            rescisao_id.company_id.cnpj_cpf
        )
        ide_estab_lot.codLotacao.valor = \
            rescisao_id.company_id.cod_lotacao

        cod_funcionario = True if rescisao_id.contract_id.category_id.code != '410' else False
        rubricas_convencao_coletiva = {}

        for rubrica_line in rescisao_id.line_ids:
            # if rubrica_line.salary_rule_id.category_id.id in (
            #         self.env.ref('hr_payroll.PROVENTO').id,
            #         self.env.ref('hr_payroll.DEDUCAO').id
            # ):
            if rubrica_line.salary_rule_id.nat_rubr:
                # if rubrica_line.salary_rule_id.code != 'PENSAO_ALIMENTICIA':
                #     if rubrica_line.total > 0:
                #
                data_apuracao, eh_periodo = \
                    self.validar_referencia_periodo_linha(
                        rubrica_line, periodo_apuracao,
                        periodo_apuracao_inverso)

                if rubrica_line.salary_rule_id.cod_inc_irrf_calculado not in \
                        ['31', '32', '33', '34', '35', '51', '52', '53', '54', '55', '81', '82', '83']:
                    if rubrica_line.total > 0:
                        condicao_pagamento_anterior = True if \
                            eh_periodo and convencao_coletiva_id and (
                                    rubrica_line.reference <= data_apuracao) \
                            and rubrica_line.salary_rule_id.category_id.code ==\
                            'PROVENTO' and cod_funcionario else False

                        if condicao_pagamento_anterior:
                            rubricas_convencao_coletiva[rubrica_line.id] = rubrica_line
                        else:
                            det_verbas = pysped.esocial.leiaute.S2299_DetVerbas_2()
                            det_verbas.codRubr.valor = \
                                rubrica_line.salary_rule_id.codigo
                            det_verbas.ideTabRubr.valor = \
                                rubrica_line.salary_rule_id.identificador
                            if rubrica_line.quantity and float(rubrica_line.quantity) != 1:
                                det_verbas.qtdRubr.valor = float(rubrica_line.quantity)
                                det_verbas.vrUnit.valor = float(rubrica_line.amount)
                            if rubrica_line.rate and rubrica_line.rate != 100:
                                det_verbas.fatorRubr.valor = rubrica_line.rate
                            det_verbas.vrRubr.valor = str(rubrica_line.total)

                            ide_estab_lot.detVerbas.append(det_verbas)

        info_ag_nocivo = pysped.esocial.leiaute.S2299_InfoAgNocivo_2()
        info_ag_nocivo.grauExp.valor = 1

        ide_estab_lot.infoAgNocivo.append(info_ag_nocivo)
        info_per_apur.ideEstabLot.append(ide_estab_lot)

        ide_dm_dev.infoPerApur.append(info_per_apur)

        if convencao_coletiva_id and rubricas_convencao_coletiva:

            info_per_ant = pysped.esocial.leiaute.S2299_InfoPerAnt_2()
            ide_adc_ant = pysped.esocial.leiaute.S2299_IdeADC_2()
            ide_adc_ant.dtAcConv.valor = \
                convencao_coletiva_id.data_assinatura_acordo
            ide_adc_ant.tpAcConv.valor = \
                convencao_coletiva_id.tipo_acordo
            ide_adc_ant.compAcConv.valor = periodo_apuracao
            ide_adc_ant.dtEfAcConv.valor = \
                convencao_coletiva_id.data_efetivacao
            ide_adc_ant.dsc.valor = convencao_coletiva_id.descricao

            periodos_pregressos = self.env['account.period'].search(
                [
                    ('date_start', '>=', '01-01-{}'.format(
                        periodo_id.code[3:])),
                    ('date_stop', '<=', periodo_id.date_stop),
                    ('special', '=', False),
                ]
            )

            for periodo in periodos_pregressos:
                if not rubricas_convencao_coletiva:
                    continue
                periodo_data = '{}-{}'.format(
                    periodo.code[3:], periodo.code[:2])
                ide_periodo = pysped.esocial.leiaute.S2299_IdePeriodo_2()
                ide_periodo.perRef.valor = periodo_data

                ide_estab_lot = \
                    pysped.esocial.leiaute.S2299_IdeEstabLot_2()
                ide_estab_lot.tpInsc.valor = '1'
                ide_estab_lot.nrInsc.valor = \
                    limpa_formatacao(self.sped_hr_rescisao_id.company_id.cnpj_cpf)
                ide_estab_lot.codLotacao.valor = \
                    self.sped_hr_rescisao_id.company_id.cod_lotacao

                # Somente para a empresa do Simples Nacional
                # ide_estab_lot.remunPerAnt.indSimples.valor = ''
                linhas_processadas = []
                for line in rubricas_convencao_coletiva:
                    if rubricas_convencao_coletiva[
                        line].reference == periodo_data:
                        itens_remun = \
                            pysped.esocial.leiaute.S2299_DetVerbas_2()
                        itens_remun.codRubr.valor = \
                            rubricas_convencao_coletiva[
                                line].salary_rule_id.codigo
                        itens_remun.ideTabRubr.valor = \
                            rubricas_convencao_coletiva[
                                line].salary_rule_id.identificador
                        if rubricas_convencao_coletiva[line].quantity and float(
                                rubricas_convencao_coletiva[
                                    line].quantity) != 1:
                            itens_remun.qtdRubr.valor = float(
                                rubricas_convencao_coletiva[line].quantity)
                            itens_remun.vrUnit.valor = \
                                formata_valor(
                                    rubricas_convencao_coletiva[line].amount)
                        if rubricas_convencao_coletiva[line].rate and \
                                rubricas_convencao_coletiva[line].rate != 100:
                            itens_remun.fatorRubr.valor = \
                            rubricas_convencao_coletiva[line].rate
                        itens_remun.vrRubr.valor = formata_valor(
                            rubricas_convencao_coletiva[line].total)
                        ide_estab_lot.detVerbas.append(itens_remun)

                        linhas_processadas.append(line)
                    elif rubricas_convencao_coletiva[
                        line].salary_rule_id.category_id.code != 'PROVENTO':
                        linhas_processadas.append(line)

                for linha in linhas_processadas:
                    del rubricas_convencao_coletiva[linha]

                if self.sped_hr_rescisao_id.contract_id.evento_esocial == 's2200':
                    info_ag_nocivo = \
                        pysped.esocial.leiaute.S2299_InfoAgNocivo_2()
                    info_ag_nocivo.grauExp.valor = 1
                    ide_estab_lot.infoAgNocivo.append(info_ag_nocivo)

                ide_periodo.ideEstabLot.append(ide_estab_lot)
                ide_adc_ant.idePeriodo.append(ide_periodo)

            info_per_ant.ideADC.append(ide_adc_ant)
            ide_dm_dev.infoPerAnt.append(info_per_ant)

        verba_rescisoria.dmDev.append(ide_dm_dev)

        outros_vinculos = self.sped_hr_rescisao_id.contract_id.contribuicao_inss_ids

        periodo_rescisao = '{:02}/{}'.format(
            self.sped_hr_rescisao_id.mes_do_ano,
            self.sped_hr_rescisao_id.ano
        )

        for vinculo in outros_vinculos:
            if not periodo_rescisao == vinculo.period_id.code:
                continue
            info_mv = pysped.esocial.leiaute.S2299_InfoMV_2()

            remun_outr_empr = \
                pysped.esocial.leiaute.S1200_RemunOutrEmpr_2()
            remun_outr_empr.tpInsc.valor = \
                vinculo.tipo_inscricao_vinculo
            remun_outr_empr.nrInsc.valor = limpa_formatacao(
                vinculo.cnpj_cpf_vinculo)
            remun_outr_empr.codCateg.valor = \
                vinculo.cod_categ_vinculo
            remun_outr_empr.vlrRemunOE.valor = \
                vinculo.valor_remuneracao_vinculo

            info_mv.remunOutrEmpr.append(remun_outr_empr)

            if vinculo.valor_alicota_vinculo >= 621.03:
                info_mv.indMV.valor = '3'
            else:
                info_mv.indMV.valor = '2'

                verba_rescisoria.infoMV.append(info_mv)

        infoDeslig.verbaResc.append(verba_rescisoria)

        return S2299, validacao

    def validar_referencia_periodo_linha(self, line, periodo_apuracao,
                                         periodo_apuracao_inverso):
        if line.reference and line.reference.replace(' ', ''):
            eh_periodo = re.search(
                '[0-9]*\d{2}[-][0-9]*\d{4}', line.reference)
            if not eh_periodo:
                eh_periodo = re.search(
                    '[0-9]*\d{4}[-][0-9]*\d{2}', line.reference)
                data_apuracao = periodo_apuracao
            else:
                data_apuracao = periodo_apuracao_inverso
        else:
            data_apuracao = False
            eh_periodo = False
        return data_apuracao, eh_periodo

    @api.multi
    def retorno_sucesso(self, evento):
        """
        :param evento:
        :return:
        """
        self.ensure_one()

        if evento:
            for tot in evento.tot:

                if tot.tipo.valor == 'S5001':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-2299'),
                        ('recibo', '=',
                         tot.eSocial.evento.ideEvento.nrRecArqBase.valor)
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5001 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.contribuicao.inss'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    periodo_id = self.periodo_id.find(
                        self.sped_hr_rescisao_id.data_afastamento)

                    # Popula os valores para criar/alterar o registro
                    # intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': periodo_id.id,
                        'sped_registro_s2299': sped_registro.id,
                        'trabalhador_id':
                            sped_registro.origem_intermediario.trabalhador_id.id,
                    }

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env['sped.contribuicao.inss'].create(
                            vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5001',
                        'evento': 'evtBasesTrab',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': ('sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'origem_intermediario': (
                                    'sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.ideEvento.nrRecArqBase.valor,
                        'trabalhador_id':
                            sped_registro.origem_intermediario.trabalhador_id.id,
                        'periodo_id': periodo_id.id,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5001:
                        sped_s5001.write(vals_registro_totalizador)
                    else:
                        sped_s5001 = self.env['sped.registro'].create(
                            vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5001 = sped_s5001

                    # Popula o intermediário S2299 com o intermediário totalizador
                    self.s5001_id = sped_intermediario

                    # Popula o intermediario do registro enviado com o
                    # totalizador obtido
                    sped_registro.sped_s5001 = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5001.consulta_xml_id:
                        consulta = sped_s5001.consulta_xml_id
                        sped_s5001.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5001.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome,
                                                          consulta_xml)
                    sped_s5001.consulta_xml_id = anexo_id

                    # Limpa a tabela sped.contribuicao.inss.infocpcal
                    for receita in sped_intermediario.infocpcalc_ids:
                        receita.unlink()

                    # Limpa a tabela sped.contribuicao.inss.ideestablot
                    for base in sped_intermediario.ideestablot_ids:
                        base.unlink()

                    # Popula a tabela sped.contribuicao.inss.infocpcal com os valores apurados no S-5001
                    for receita in tot.eSocial.evento.infoCpCalc:
                        vals = {
                            'parent_id': sped_intermediario.id,
                            'tp_cr': receita.tpCR.valor,
                            'vr_cp_seg': float(receita.vrCpSeg.valor),
                            'vr_desc_seg': float(receita.vrDescSeg.valor),
                        }
                        self.env['sped.contribuicao.inss.infocpcalc'].create(vals)

                    # Popula a tabela sped.contribuicao.inss.ideestablot
                    for estabelecimento in tot.eSocial.evento.infoCp.ideEstabLot:
                        for categoria in estabelecimento.infoCategIncid:
                            for base in categoria.infoBaseCS:
                                vals = {
                                    'parent_id': sped_intermediario.id,
                                    'tp_insc': estabelecimento.tpInsc.valor,
                                    'nr_insc': estabelecimento.nrInsc.valor,
                                    'cod_lotacao': estabelecimento.codLotacao.valor,
                                    'matricula': categoria.matricula.valor,
                                    'cod_categ': categoria.codCateg.valor,
                                    'ind13': base.ind13.valor,
                                    'tp_valor': base.tpValor.valor,
                                    'valor': float(base.valor.valor),
                                }
                                if categoria.indSimples:
                                    vals['ind_simples'] = categoria.indSimples.valor

                                self.env['sped.contribuicao.inss.ideestablot'].create(vals)

                    # Adiciona o S-5001 ao Período do e-Social que gerou o S-2299 relacionado
                    periodo = self.env['sped.esocial'].search([
                        ('company_id', '=', self.company_id.id),
                        ('periodo_id', '=', periodo_id.id),
                    ])

                    if periodo:
                        periodo.inss_trabalhador_ids = [(4, sped_intermediario.id)]

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.sped_hr_rescisao_id.contract_id.employee_id
