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


class SpedEsocialPagamento(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.pagamento"
    _rec_name = "codigo"
    _order = "company_id,periodo_id,beneficiario_id"

    codigo = fields.Char(
        string='Código',
        compute='_compute_codigo',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    beneficiario_id = fields.Many2one(
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
    contratos = fields.Integer(
        string='Contratos',
        compute='_compute_qtd',
    )
    pagamentos = fields.Integer(
        string='Remunerações',
        compute='_compute_qtd',
    )

    @api.depends('company_id', 'beneficiario_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
            if esocial.company_id:
                codigo += esocial.company_id.name or ''
            if esocial.beneficiario_id:
                codigo += ' - ' if codigo else ''
                codigo += esocial.beneficiario_id.name or ''
            if esocial.periodo_id:
                codigo += ' ' if codigo else ''
                codigo += '('
                codigo += esocial.periodo_id.code or ''
                codigo += ')'
            esocial.codigo = codigo

    @api.depends('contract_ids', 'payslip_ids')
    def _compute_qtd(self):
        for esocial in self:
            esocial.contratos = 0 if not esocial.contract_ids else len(esocial.contract_ids)
            esocial.pagamentos = 0 if not esocial.payslip_ids else len(esocial.payslip_ids)

    # Campos de controle e-Social, registros Periódicos
    sped_registro = fields.Many2one(
        string='Registro SPED',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        string='Situação',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
            ('5', 'Precisa Retificar'),
        ],
        related='sped_registro.situacao',
    )

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def atualizar_esocial(self):
        self.ensure_one()

        # Criar o registro S-1210
        if not self.sped_registro:
            values = {
                'tipo': 'esocial',
                'registro': 'S-1210',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'na',
                'evento': 'evtPgtos',
                'origem': ('sped.esocial.pagamento,%s' % self.id),
                'origem_intermediario': ('sped.esocial.pagamento,%s' % self.id),
            }

            sped_registro = self.env['sped.registro'].create(values)
            self.sped_registro = sped_registro

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        self.ensure_one()

        # Cria o registro
        S1210 = pysped.esocial.leiaute.S1210_2()
        S1210.tpInsc = '1'
        S1210.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        S1210.evento.ideEvento.indRetif.valor = '1'  # TODO Criar meio de enviar um registro retificador
        # S1210.evento.ideEvento.nrRecibo.valor = '' # Recibo só quando for retificação
        S1210.evento.ideEvento.indApuracao.valor = '1'  # TODO Lidar com os holerites de 13º salário
                                                        # '1' - Mensal
                                                        # '2' - Anual (13º salário)
        S1210.evento.ideEvento.perApur.valor = \
            self.periodo_id.code[3:7] + '-' + \
            self.periodo_id.code[0:2]
        S1210.evento.ideEvento.tpAmb.valor = ambiente
        S1210.evento.ideEvento.procEmi.valor = '1'    # Aplicativo do empregador
        S1210.evento.ideEvento.verProc.valor = '8.0'  # Odoo v.8.0

        # Popula ideEmpregador (Dados do Empregador)
        S1210.evento.ideEmpregador.tpInsc.valor = '1'
        S1210.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideBenef (Dados do Beneficiário do Pagamento)
        S1210.evento.ideBenef.cpfBenef.valor = limpa_formatacao(self.beneficiario_id.cpf)

        # Popula deps (Informações de dependentes do beneficiário do pagamento
        # Conta o número de dependentes para fins do regime próprio de previdência social
        dependentes = 0
        for dependente in self.beneficiario_id.dependent_ids:
            if dependente.dependent_verification:
                dependentes += 1

        if dependentes:

            # Popula o valor de dedução por dependente no período selecionado
            valor = 0
            domain = [
                ('year', '=', int(self.periodo_id.fiscalyear_id.code)),
            ]
            deducao = self.env['l10n_br.hr.income.tax.deductable.amount.family'].search(domain)
            if deducao:
                valor = deducao.amount

            S1210.evento.ideBenef.vrDedDep.valor = formata_valor(dependentes * valor)

        # Popula infoPgto (1 para cada payslip)
        for payslip in self.payslip_ids:
            info_pgto = pysped.esocial.leiaute.S1210_InfoPgto_2()

            # TODO Identificar a data do pagamento de acordo com o arquivo CNAB
            # Por enquanto vou usar a data final do período ou a data atual (a que for menor)
            data = fields.Date.today()
            fim_periodo = self.periodo_id.date_stop
            if fim_periodo < data:
                data = fim_periodo
            info_pgto.dtPgto.valor = data

            # Identifica o tpPgto dependendo do campo tipo_de_folha e tp_reg_prev
            # 1 - Pagamento de remuneração, conforme apurado em {dmDev} do S-1200;
            # 2 - Pagamento de verbas rescisórias conforme apurado em {dmDev} do S-2299;
            # 3 - Pagamento de verbas rescisórias conforme apurado em {dmDev} do S-2399;
            # 5 - Pagamento de remuneração conforme apurado em {dmDev} do S-1202;
            # 6 - Pagamento de Benefícios Previdenciários, conforme apurado em {dmDev} do S-1207;
            # 7 - Recibo de férias;
            # 9 - Pagamento relativo a competências anteriores ao início da obrigatoriedade dos eventos
            #     periódicos para o contribuinte;
            #
            tipo = '1'
            if payslip.tipo_de_folha == 'rescisao':
                tipo = '2'
            if payslip.contract_id.tp_reg_prev == '2':
                tipo = '5'
            if payslip.tipo_de_folha == 'ferias':
                tipo = '7'
            info_pgto.tpPgto.valor = tipo
            info_pgto.indResBr.valor = 'S'  # TODO Lidar com pagamentos a pessoas do exterior quando o Odoo
                                            # tiver isso disponível

            if tipo != '7':
                # Popula detPgtoFl
                det_pgto_fl = pysped.esocial.leiaute.S1210_DetPgtoFl_2()
                periodo = self.periodo_id.code[3:7] + '-' + self.periodo_id.code[0:2] \
                    if payslip.tipo_de_folha != 'decimo_terceiro' else self.periodo_id.fiscalyear_id.code
                det_pgto_fl.perRef.valor = periodo
                det_pgto_fl.ideDmDev.valor = payslip.number
                det_pgto_fl.indPgtoTt.valor = 'S'  # TODO Lidar com pagamento de adiantamentos mensais, quando tivermos
                det_pgto_fl.vrLiq.valor = formata_valor(payslip.total_folha)

                # Pega o número do recibo do S-2299 (se for o caso)
                if tipo == '2':
                    recibo = payslip.sped_s2299.sped_s2299_registro_inclusao.recibo
                    if payslip.sped_s2299.sped_s2299_registro_retificacao:
                        ultima_alteracao = payslip.sped_s2299.sped_s2299_registro_inclusao.sorted(
                            key=lambda r: r.data_hora_transmissao, reverse=True)
                        recibo = ultima_alteracao[0].recibo
                    det_pgto_fl.nrRecArq.valor = recibo

                # Popula infoPgto.detPgtoFl.retPgtoTot
                for line in payslip.line_ids:

                    # Somente pega as Rubricas de Retenção de IRRF e Pensão Alimentícia
                    if line.salary_rule_id.cod_inc_irrf_calculado in \
                            ['31', '32', '33', '34', '35', '51', '52', '53', '54', '55', '81', '82', '83']:

                        ret_pgto_tot = pysped.esocial.leiaute.S1210_RetPgtoTot_2()
                        ret_pgto_tot.codRubr.valor = line.salary_rule_id.codigo
                        ret_pgto_tot.ideTabRubr.valor = line.salary_rule_id.identificador
                        if line.quantity and float(line.quantity) != 1:
                            ret_pgto_tot.qtdRubr.valor = float(line.quantity)
                            ret_pgto_tot.vrUnit.valor = formata_valor(line.amount)
                        if line.rate and line.rate != 100:
                            ret_pgto_tot.fatorRubr.valor = line.rate
                        ret_pgto_tot.vrRubr.valor = formata_valor(line.total)

                        if line.salary_rule_id.cod_inc_irrf_calculado in ['51', '52', '53', '54', '55']:
                            pen_alim = pysped.esocial.leiaute.S1210_PenAlim_2()
                            pen_alim.cpfBenef.valor = limpa_formatacao(line.partner_id.cnpj_cpf)
                            # dtNasctoBenef  # TODO Hoje não estou enviando porque não temos esse controle no Odoo
                            pen_alim.nmBenefic.valor = line.partner_id.name
                            pen_alim.vlrPensao.valor = formata_valor(line.total)
                            ret_pgto_tot.penAlim.append(pen_alim)

                        det_pgto_fl.retPgtoTot.append(ret_pgto_tot)

                # Popula a tag detPgtoFl
                info_pgto.detPgtoFl.append(det_pgto_fl)
            else:
                # Popula a tag detPgtoFer
                det_pgto_fer = pysped.esocial.leiaute.S1210_DetPgtoFer_2()
                det_pgto_fer.codCateg.valor = payslip.contract_id.categoria
                det_pgto_fer.matricula.valor = payslip.contract_id.matricula
                det_pgto_fer.dtIniGoz.valor = payslip.date_from
                info_pgto.detPgtoFer.append(det_pgto_fer)

                # Pega o valor calculo 'FERIAS' do campo worked_days_line_ids
                dias = 0
                for item in payslip.worked_days_line_ids:
                    if item.code == 'FERIAS':
                        dias = item.number_of_days
                det_pgto_fer.qtdDias.valor = dias

                det_pgto_fer.vrLiq.valor = formata_valor(payslip.total_folha)

                # Popula detPgtoFer.detRubrFer
                for line in payslip.line_ids:

                    # Somente pega as Rubricas de Retenção de IRRF e Pensão Alimentícia
                    if line.salary_rule_id.cod_inc_irrf_calculado in \
                            ['00', '01', '09', '13', '33', '43', '46', '53', '63', '75', '93']:

                        det_rubr_fer = pysped.esocial.leiaute.S1210_DetRubrFer_2()
                        det_rubr_fer.codRubr.valor = line.salary_rule_id.codigo
                        det_rubr_fer.ideTabRubr.valor = line.salary_rule_id.identificador
                        if line.quantity and float(line.quantity) != 1:
                            det_rubr_fer.qtdRubr.valor = float(line.quantity)
                            det_rubr_fer.vrUnit.valor = formata_valor(line.amount)
                        if line.rate and line.rate != 100:
                            det_rubr_fer.fatorRubr.valor = line.rate
                        det_rubr_fer.vrRubr.valor = formata_valor(line.total)

                        if line.salary_rule_id.cod_inc_irrf_calculado in ['53']:
                            pen_alim = pysped.esocial.leiaute.S1210_DetRubrFerPenAlim_2()
                            pen_alim.cpfBenef.valor = limpa_formatacao(line.partner_id.cnpj_cpf)
                            # dtNasctoBenef  # TODO Hoje não estou enviando porque não temos esse controle no Odoo
                            pen_alim.nmBenefic.valor = line.partner_id.name
                            pen_alim.vlrPensao.valor = formata_valor(line.total)
                            det_rubr_fer.penAlim.append(pen_alim)

                        det_pgto_fer.detRubrFer.append(det_rubr_fer)

                # Popula a tag detPgtoFl
                info_pgto.detPgtoFer.append(det_pgto_fer)

            # Popula infoPgto
            S1210.evento.ideBenef.infoPgto.append(info_pgto)

        return S1210

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()
