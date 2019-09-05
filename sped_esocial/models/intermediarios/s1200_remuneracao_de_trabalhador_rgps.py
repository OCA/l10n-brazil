# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao
from pybrasil.valor import formata_valor
from datetime import datetime
import pysped


class SpedEsocialRemuneracao(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.remuneracao"
    _rec_name = "codigo"
    _order = "company_id,periodo_id,trabalhador_id"

    codigo = fields.Char(
        string='Código',
        compute='_compute_codigo',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    trabalhador_id = fields.Many2one(
        string='Trabalhador',
        comodel_name='hr.employee',
    )
    periodo_id = fields.Many2one(
        string='Período',
        comodel_name='account.period',
    )
    contract_ids = fields.Many2many(
        string='Contratos',
        comodel_name='hr.contract',
    )
    payslip_ids = fields.Many2many(
        string='Holerites',
        comodel_name='hr.payslip',
    )
    payslip_autonomo_ids = fields.Many2many(
        string='Holerites de Autônomos',
        comodel_name='hr.payslip.autonomo',
    )
    contratos = fields.Integer(
        string='Contratos',
        compute='_compute_qtd',
    )
    remuneracoes = fields.Integer(
        string='Remunerações',
        compute='_compute_qtd',
    )
    s5001_id = fields.Many2one(
        string='S-5001 (Contribuições Sociais)',
        comodel_name='sped.contribuicao.inss',
    )

    @api.depends('company_id', 'trabalhador_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
            if esocial.trabalhador_id:
                codigo += ' - ' if codigo else ''
                codigo += esocial.trabalhador_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '('
                codigo += esocial.periodo_id.code or ''
                codigo += ')'
            esocial.codigo = codigo

    @api.depends('contract_ids', 'payslip_ids', 'payslip_autonomo_ids')
    def _compute_qtd(self):
        for esocial in self:
            esocial.contratos = 0 if not esocial.contract_ids else len(esocial.contract_ids)
            esocial.remuneracoes = 0 if not esocial.payslip_ids else len(esocial.payslip_ids)
            esocial.remuneracoes_autonomos = 0 if not esocial.payslip_autonomo_ids else len(esocial.payslip_autonomo_ids)

    # Campos de controle e-Social, registros Periódicos
    sped_registro = fields.Many2one(
        string='Registro SPED',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        string='Situação',
        selection=[
            ('0', 'Sem Registro'),
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
            ('6', 'Retificado'),
            ('7', 'Excluido'),
        ],
        compute='_compute_situacao'
    )
    sped_registro_excluido_ids = fields.Many2many(
        string=u'Registros Excluídos',
        comodel_name='sped.registro',
    )

    @api.multi
    def _compute_situacao(self):
        for record in self:
            if record.sped_registro:
                record.situacao_esocial = record.sped_registro.situacao
            elif record.sped_registro_excluido_ids:
                record.situacao_esocial = '7'
            else:
                record.situacao_esocial = '0'

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_esocial(self):
        self.ensure_one()

        # Criar o registro S-1200
        if not self.sped_registro:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1200',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'na',
                'evento': 'evtRemun',
                'origem': ('sped.esocial.remuneracao,%s' % self.id),
                'origem_intermediario': ('sped.esocial.remuneracao,%s' % self.id),
            }

            sped_registro = self.env['sped.registro'].create(values)
            self.sped_registro = sped_registro

    def verificar_rubricas_ferias_holerite(self, rubrica):
        rubricas_ferias = [
            self.env.ref('sped_tabelas.tab03_1020').id,
            self.env.ref('sped_tabelas.tab03_1021').id,
            self.env.ref('sped_tabelas.tab03_1022').id,
            self.env.ref('sped_tabelas.tab03_1023').id,
            self.env.ref('sped_tabelas.tab03_1024').id,
        ]

        if rubrica.nat_rubr.id in rubricas_ferias:
            return True

        return False

    @api.multi
    def popula_xml(self, ambiente='2', operacao='na'):
        self.ensure_one()

        convencao_coletiva_id = self.env['l10n.br.hr.acordo.coletivo'].search(
            [('competencia_pagamento', '=', self.periodo_id.id)])

        periodo_apuracao = self.periodo_id.code[3:7] + '-' + \
                self.periodo_id.code[0:2]

        periodo_apuracao_inverso = self.periodo_id.code[0:2] + '-' + \
                                   self.periodo_id.code[3:7]

        # Validação
        validacao = ""

        # Cria o registro
        S1200 = pysped.esocial.leiaute.S1200_2()
        S1200.tpInsc = '1'
        S1200.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        indRetif = '1'
        if operacao == 'R':
            indRetif = '2'
            registro_para_retificar = self.sped_registro
            tem_retificacao = True
            while tem_retificacao:
                if registro_para_retificar.retificacao_ids and \
                        registro_para_retificar.retificacao_ids[
                            0].situacao not in ['1', '3']:
                    registro_para_retificar = \
                    registro_para_retificar.retificacao_ids[0]
                else:
                    tem_retificacao = False
            S1200.evento.ideEvento.nrRecibo.valor = registro_para_retificar.recibo
        S1200.evento.ideEvento.indRetif.valor = indRetif
        
        if not int(self.periodo_id.code.split('/')[0]) == 13:
            S1200.evento.ideEvento.indApuracao.valor = '1'
            S1200.evento.ideEvento.perApur.valor = periodo_apuracao
        else:
            S1200.evento.ideEvento.indApuracao.valor = '2'
            S1200.evento.ideEvento.perApur.valor = self.periodo_id.code[3:7]

        ind_apuracao = False
        per_apur = False

        remuneracoes_ids = self.payslip_ids or self.payslip_autonomo_ids
        for remuneracao in remuneracoes_ids:
            if remuneracao.tipo_de_folha == 'decimo_terceiro':
                ind_apuracao = '2'
                per_apur = self.periodo_id.code[3:7]
                break

        if not (ind_apuracao and per_apur):
            ind_apuracao = '1'
            per_apur = self.periodo_id.code[3:7] + '-' + self.periodo_id.code[0:2]

        S1200.evento.ideEvento.indApuracao.valor = ind_apuracao
        S1200.evento.ideEvento.perApur.valor = per_apur
        S1200.evento.ideEvento.tpAmb.valor = ambiente
        S1200.evento.ideEvento.procEmi.valor = '1'    # Aplicativo do empregador
        S1200.evento.ideEvento.verProc.valor = 'Odoo v.8.0'  # Odoo v.8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1200.evento.ideEmpregador.tpInsc.valor = '1'
        S1200.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideTrabalhador (Dados do Trabalhador)
        S1200.evento.ideTrabalhador.cpfTrab.valor = limpa_formatacao(self.trabalhador_id.cpf)
        S1200.evento.ideTrabalhador.nisTrab.valor = limpa_formatacao(self.trabalhador_id.pis_pasep)

        for contrato in self.trabalhador_id.contract_ids:
            if contrato.contribuicao_inss_ids:
                for vinculo in contrato.contribuicao_inss_ids:
                    if not vinculo.period_id.id == self.periodo_id.id:
                        continue

                    info_mv = pysped.esocial.leiaute.S1200_InfoMV_2()

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

                    S1200.evento.ideTrabalhador.infoMV.append(info_mv)

        # # Popula ideTrabalhador.infoComplem               # TODO
        # #        ideTrabalhador.infoComplem.sucessaoVinc
        # #
        # # Registro preenchido exclusivamente quando o evento de remuneração referir-se a trabalhador cuja
        # # categoria não está sujeita ao evento de admissão ou ao evento de início de "trabalhador sem vínculo".
        # # No caso das categorias em que o envio do evento TSV é opcional, o preenchimento do grupo somente é
        # # exigido se não houver evento TSV Início correspondente (cpf + categoria). As informações
        # # complementares são necessárias para correta identificação do trabalhador.
        #
        # info_complem = pysped.esocial.leiaute.S1200_InfoComplem_2()
        # info_complem.

        # # Popula ideTrabalhador.procJudTrab  # TODO
        # #
        # # Informações sobre a existência de processos judiciais do trabalhador com decisão favorável quanto à não
        # # incidência ou alterações na incidência de contribuições sociais e/ou Imposto de Renda sobre as rubricas
        # # apresentadas nos subregistros de {dmDev}.
        #
        # proc_jud_trab = pysped.esocial.leiaute.S1200_ProcJudTrab_2()
        # proc_jud_trab.

        # # Popula ideTrabalhador.infoInterm  # TODO
        # #
        # # Informações relativas ao trabalho intermitente
        #
        # info_interm = pysped.esocial.leiaute.S1200_InfoInterm_2()
        # info_interm.

        # Popula dmDev (1 para cada payslip)
        ind_apur = True if \
            S1200.evento.ideEvento.indApuracao.valor == '1' \
            else False

        cod_funcionario = True if contrato.category_id.code != '410' else False

        remuneracoes_ids = self.payslip_ids or self.payslip_autonomo_ids
        for payslip in remuneracoes_ids:
            rubricas_convencao_coletiva = {}
            if payslip.tipo_de_folha == 'ferias':
                continue
            dm_dev = pysped.esocial.leiaute.S1200_DmDev_2()
            dm_dev.ideDmDev.valor = payslip.number
            dm_dev.codCateg.valor = payslip.contract_id.category_id.code  # TODO Integrar com a tabela 01 do e-Social

            if not payslip.contract_id.date_end:
                # Popula dmDev.infoPerApur
                info_per_apur = pysped.esocial.leiaute.S1200_InfoPerApur_2()
                info_per_apur.ideEstabLot.tpInsc.valor = '1'  # CNPJ
                info_per_apur.ideEstabLot.nrInsc.valor = limpa_formatacao(payslip.company_id.cnpj_cpf)
                info_per_apur.ideEstabLot.codLotacao.valor = payslip.company_id.cod_lotacao

                # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur
                remun_per_apur = pysped.esocial.leiaute.S1200_RemunPerApur_2()

                # Só preencher matricula de EMPREGADO com vinculo
                if payslip.contract_id.evento_esocial == 's2200':
                    remun_per_apur.matricula.valor = payslip.contract_id.matricula

            # Somente para quando a empresa for do Simples
            # remun_per_apur.indSimples.valor =

            # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.itensRemun
            for line in payslip.line_ids:
                # Só adiciona a rubrica se o campo nat_rubr estiver definido, isso define que a rubrica deve
                # ser transmitida para o e-Social.
                if line.salary_rule_id.nat_rubr:
                    if payslip.tipo_de_folha == 'decimo_terceiro':
                        if line.salary_rule_id.code == 'INSS':
                            continue

                    data_apuracao, eh_periodo = \
                        self.validar_referencia_periodo_linha(
                            line, periodo_apuracao, periodo_apuracao_inverso)

                    if not eh_periodo:
                        if self.verificar_rubricas_ferias_holerite(
                                line.salary_rule_id):
                            continue

                    if line.salary_rule_id.cod_inc_irrf_calculado not in \
                            ['31', '32', '33', '34', '35', '51', '52', '53', '54', '55', '81', '82', '83']:
                        if line.salary_rule_id.cod_inc_irrf_calculado == '13' \
                                and not eh_periodo:
                            continue

                        condicao_pagamento_anterior = True if eh_periodo and \
                            convencao_coletiva_id and (
                                line.reference <= data_apuracao) and \
                            line.salary_rule_id.category_id.code in ['PROVENTO', 'INSS']\
                            and ind_apur and cod_funcionario else False

                        if condicao_pagamento_anterior:
                            rubricas_convencao_coletiva[line.id] = line
                        else:
                            if payslip.contract_id.date_end:
                                continue

                            if line.salary_rule_id.code == 'BASE_INSS' and \
                                    line.slip_id.tipo_de_folha == 'ferias':
                                continue

                            if line.total != 0:

                                itens_remun = pysped.esocial.leiaute.S1200_ItensRemun_2()
                                itens_remun.codRubr.valor = line.salary_rule_id.codigo
                                itens_remun.ideTabRubr.valor = line.salary_rule_id.identificador
                                if line.quantity and float(line.quantity) != 1:
                                    itens_remun.qtdRubr.valor = float(line.quantity)
                                    itens_remun.vrUnit.valor = formata_valor(line.amount)
                                if line.rate and line.rate != 100:
                                    itens_remun.fatorRubr.valor = line.rate
                                itens_remun.vrRubr.valor = formata_valor(line.total)
                                remun_per_apur.itensRemun.append(itens_remun)

            # # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoSaudeColet  # TODO Quando tivermos plano de saúde
            # #                                                                   # coletívo
            # # Informações de plano privado coletivo empresarial de assistência à saúde. Só preencher se houver
            # # {codRubr} em {itensRemun}, cuja natureza de rubrica {natRubr} indicada em S-1010 seja igual a [9219].
            # # Não preencher nos demais casos
            # #
            # info_saude_colet = pysped.esocial.leiaute.S1200_InfoSaudeColet_2()
            # info_saude_colet.

            # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoAgNocivo  # TODO Quando tivermos controle de
            #                                                                 # agentes nocivos
            # Registro preenchido exclusivamente em relação a remuneração do trabalhador enquadrado em uma das
            # categorias relativas a Empregado, Servidor Público, Avulso, ou na categoria de Cooperado filiado
            # a cooperativa de produção [738] ou Cooperado filiado a cooperativa de trabalho que presta serviço
            # a empresa [731, 734], permitindo o detalhamento do grau de exposição do trabalhador aos agentes
            # nocivos que ensejam cobrança da contribuição adicional para financiamento dos benefícios de
            # aposentadoria especial.
            #

            if not payslip.contract_id.date_end:
                # Preencher com o código que representa o grau de exposição a
                # agentes nocivos, conforme tabela 2. Preencher apenas para
                # trabalhadores com vinculo S2200
                if payslip.contract_id.evento_esocial == 's2200':
                    info_ag_nocivo = pysped.esocial.leiaute.S1200_InfoAgNocivo_2()
                    # Inserir um campo em algum lugar (no contrato talvez)
                    info_ag_nocivo.grauExp.valor = 1
                    remun_per_apur.infoAgNocivo.append(info_ag_nocivo)

            # # Popula dmDev.infoPerApur.ideEstabLot.remunPerApur.infoTrabInterm  # TODO Quando tivermos controle
            # #                                                                   # trabalho intermitente
            # # Informações da(s) convocação(ões) de trabalho intermitente
            # #
            # info_trab_interm = pysped.esocial.leiaute.S1200_InfoTrabInterm_2()
            # info_trab_interm.

            # # Popula dmDev.infoPerAnt  # TODO Quando tratarmos dos cálculo retroativos por coleção coletiva
            # #
            # # Registro destinado ao registro de:
            # # a) remuneração relativa a diferenças salariais provenientes de acordos coletivos, convenção coletiva
            # #    e dissídio.
            # # b) remuneração relativa a diferenças de vencimento provenientes de disposições legais (órgãos públicos)
            # # c) bases de cálculo para efeitos de apuração de FGTS resultantes de conversão de licença saúde em
            # #    acidente de trabalho
            # # d) verbas de natureza salarial ou não salarial devidas após o desligamento.
            # # OBS.: as informações previstas nos itens "a", "b" e "d" acima podem se referir ao período de apuração
            # #       definido em {perApur} ou a períodos anteriores a {perApur}.
            # #
            if convencao_coletiva_id and rubricas_convencao_coletiva:

                info_per_ant = pysped.esocial.leiaute.S1200_InfoPerAnt_2()
                ide_adc_ant = pysped.esocial.leiaute.S1200_IdeADC_2()
                # ide_adc_ant.dtAcConv.valor = \
                #     convencao_coletiva_id.data_assinatura_acordo
                ide_adc_ant.tpAcConv.valor = \
                    convencao_coletiva_id.tipo_acordo
                # ide_adc_ant.compAcConv.valor = periodo_apuracao
                # ide_adc_ant.dtEfAcConv.valor = \
                #     convencao_coletiva_id.data_efetivacao
                ide_adc_ant.dsc.valor = convencao_coletiva_id.descricao
                ide_adc_ant.remunSuc.valor = \
                    convencao_coletiva_id.remuneracao_relativa_sucessao

                periodos_pregressos = self.env['account.period'].search(
                    [
                        ('date_start', '>=', '01-01-{}'.format(
                            self.periodo_id.code[3:])),
                        ('date_stop', '<=', self.periodo_id.date_stop),
                        ('special', '=', False),
                    ], order='date_start ASC'
                )

                for periodo in periodos_pregressos:
                    if not rubricas_convencao_coletiva:
                        continue
                    periodo_data = '{}-{}'.format(
                        periodo.code[3:], periodo.code[:2])
                    periodo_data_inverso = '{}-{}'.format(
                        periodo.code[:2],periodo.code[3:])
                    ide_periodo = pysped.esocial.leiaute.S1200_IdePeriodo_2()
                    ide_periodo.perRef.valor = periodo_data

                    ide_estab_lot = \
                        pysped.esocial.leiaute.S1200_IdePeriodoIdeEstabLot_2()
                    ide_estab_lot.tpInsc.valor = '1'
                    ide_estab_lot.nrInsc.valor = \
                        limpa_formatacao(payslip.company_id.cnpj_cpf)
                    ide_estab_lot.codLotacao.valor = \
                        payslip.company_id.cod_lotacao

                    ide_estab_lot.remunPerAnt.matricula.valor = \
                        payslip.contract_id.matricula
                    # Somente para a empresa do Simples Nacional
                    # ide_estab_lot.remunPerAnt.indSimples.valor = ''
                    linhas_processadas = []
                    for line_holerite in rubricas_convencao_coletiva:
                        if rubricas_convencao_coletiva[line_holerite].reference == periodo_data or \
                                rubricas_convencao_coletiva[line_holerite].reference == periodo_data_inverso:
                            itens_remun = \
                                pysped.esocial.leiaute.S1200_ItensRemun_2()
                            itens_remun.codRubr.valor = \
                                rubricas_convencao_coletiva[line_holerite].salary_rule_id.codigo
                            itens_remun.ideTabRubr.valor = \
                                rubricas_convencao_coletiva[line_holerite].salary_rule_id.identificador
                            if rubricas_convencao_coletiva[line_holerite].quantity and float(rubricas_convencao_coletiva[line_holerite].quantity) != 1:
                                itens_remun.qtdRubr.valor = float(rubricas_convencao_coletiva[line_holerite].quantity)
                                itens_remun.vrUnit.valor = \
                                    formata_valor(rubricas_convencao_coletiva[line_holerite].amount)
                            if rubricas_convencao_coletiva[line_holerite].rate and rubricas_convencao_coletiva[line_holerite].rate != 100:
                                itens_remun.fatorRubr.valor = rubricas_convencao_coletiva[line_holerite].rate
                            itens_remun.vrRubr.valor = formata_valor(rubricas_convencao_coletiva[line_holerite].total)
                            ide_estab_lot.remunPerAnt.itensRemun.append(
                                itens_remun)

                            linhas_processadas.append(line_holerite)
                        elif rubricas_convencao_coletiva[line_holerite].salary_rule_id.category_id.code not in ['PROVENTO', 'INSS']:
                            linhas_processadas.append(line_holerite)

                    for linha in linhas_processadas:
                        del rubricas_convencao_coletiva[linha]

                    if payslip.contract_id.evento_esocial == 's2200':
                        info_ag_nocivo = \
                            pysped.esocial.leiaute.S1200_InfoAgNocivo_2()
                        info_ag_nocivo.grauExp.valor = 1
                        ide_estab_lot.remunPerAnt.infoAgNocivo.append(
                            info_ag_nocivo)

                    if ide_estab_lot.remunPerAnt.itensRemun:
                        ide_periodo.ideEstabLot.append(ide_estab_lot)
                        ide_adc_ant.idePeriodo.append(ide_periodo)

                info_per_ant.ideADC.append(ide_adc_ant)
                dm_dev.infoPerAnt.append(info_per_ant)
            # Popula dmDev.infoComplCont  # Não teremos registros no odoo que não tenham um S2300 nesses casos
            #

            if not payslip.contract_id.date_end:
                # Adiciona o registro nas listas das tags superiores
                info_per_apur.ideEstabLot.remunPerApur.append(remun_per_apur)
                dm_dev.infoPerApur.append(info_per_apur)
            S1200.evento.dmDev.append(dm_dev)

        return S1200, validacao

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
        self.ensure_one()

        if evento:
            for tot in evento.tot:

                if tot.tipo.valor == 'S5001':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-1200'),
                        ('recibo', '=', tot.eSocial.evento.ideEvento.nrRecArqBase.valor)
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5001 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.contribuicao.inss'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Popula os valores para criar/alterar o registro intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': sped_registro.origem_intermediario.periodo_id.id,
                        'trabalhador_id': sped_registro.origem_intermediario.trabalhador_id.id,
                        'sped_registro_s1200': sped_registro.id,
                    }

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env['sped.contribuicao.inss'].create(vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5001',
                        'evento': 'evtBasesTrab',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': ('sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'origem_intermediario': ('sped.contribuicao.inss,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.ideEvento.nrRecArqBase.valor,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5001:
                        sped_s5001.write(vals_registro_totalizador)
                    else:
                        sped_s5001 = self.env['sped.registro'].create(vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5001 = sped_s5001

                    # Popula o intermediário S1200 com o intermediário totalizador
                    self.s5001_id = sped_intermediario

                    # Popula o intermediario do sped.registro enviado com o
                    # totalizador 5001 retornado
                    sped_registro.sped_s5001 = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5001.consulta_xml_id:
                        consulta = sped_s5001.consulta_xml_id
                        sped_s5001.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5001.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome, consulta_xml)
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

                    # Adiciona o S-5001 ao Período do e-Social que gerou o S-1200 relacionado
                    periodo = self.env['sped.esocial'].search([
                        ('company_id', '=', self.company_id.id),
                        ('periodo_id', '=', self.periodo_id.id),
                    ])
                    periodo.inss_trabalhador_ids = [(4, sped_intermediario.id)]

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.trabalhador_id
