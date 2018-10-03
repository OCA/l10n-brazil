# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.addons.sped_transmissao.models.intermediarios.sped_registro_intermediario import SpedRegistroIntermediario

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
    payslip_autonomo_ids = fields.Many2many(
        string='Holerites',
        comodel_name='hr.payslip.autonomo',
    )
    contratos = fields.Integer(
        string='Contratos',
        compute='_compute_qtd',
    )
    pagamentos = fields.Integer(
        string='Remunerações',
        compute='_compute_qtd',
    )
    s5002_id = fields.Many2one(
        string='S-5002 (IRRF)',
        comodel_name='sped.irrf',
    )

    @api.depends('company_id', 'beneficiario_id', 'periodo_id')
    def _compute_codigo(self):
        for esocial in self:
            codigo = ''
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
        store=True,
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
    def popula_xml(self, ambiente='2', operacao='na'):
        self.ensure_one()

        # Validação
        validacao = ""

        # Cria o registro
        S1210 = pysped.esocial.leiaute.S1210_2()
        S1210.tpInsc = '1'
        S1210.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        # Popula ideEvento
        indRetif = '1'
        if operacao == 'R':
            indRetif = '2'
            # Identifica o Recibo a ser retificado
            registro_para_retificar = self.sped_registro
            tem_retificacao = True
            while tem_retificacao:
                if registro_para_retificar.retificacao_ids and \
                        registro_para_retificar.retificacao_ids[0].situacao not in ['1', '3']:
                    registro_para_retificar = registro_para_retificar.retificacao_ids[0]
                else:
                    tem_retificacao = False
            S1210.evento.ideEvento.nrRecibo.valor = registro_para_retificar.recibo
        S1210.evento.ideEvento.indRetif.valor = indRetif
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
        for payslip in self.payslip_ids or self.payslip_autonomo_ids:

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

                if payslip.tipo_de_folha == 'decimo_terceiro':
                    periodo = self.periodo_id.fiscalyear_id.code
                elif payslip.tipo_de_folha == 'rescisao':
                    periodo = ''
                else:
                    periodo = self.periodo_id.code[3:7] + '-' + \
                              self.periodo_id.code[0:2]
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
                    if line.total and line.salary_rule_id.cod_inc_irrf_calculado in \
                            ['31', '32', '34', '35', '51', '52', '53', '54', '55', '81', '82', '83']:

                        ret_pgto_tot = pysped.esocial.leiaute.S1210_RetPgtoTot_2()
                        ret_pgto_tot.codRubr.valor = line.salary_rule_id.codigo
                        ret_pgto_tot.ideTabRubr.valor = line.salary_rule_id.identificador
                        if line.quantity and float(line.quantity) != 1:
                            ret_pgto_tot.qtdRubr.valor = float(line.quantity)
                            ret_pgto_tot.vrUnit.valor = formata_valor(line.amount)
                        if line.rate and line.rate != 100:
                            ret_pgto_tot.fatorRubr.valor = formata_valor(line.rate)
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
                if payslip.contract_id.evento_esocial == 's2200':
                    det_pgto_fer.matricula.valor = payslip.contract_id.matricula
                # det_pgto_fer.matricula.valor = payslip.contract_id.matricula
                det_pgto_fer.dtIniGoz.valor = payslip.date_from
                # info_pgto.detPgtoFer.append(det_pgto_fer)

                # Pega o valor calculo 'FERIAS' do campo worked_days_line_ids
                dias = 0
                for item in payslip.worked_days_line_ids:
                    if item.code == 'FERIAS':
                        dias = item.number_of_days
                det_pgto_fer.qtDias.valor = str(int(dias))

                det_pgto_fer.vrLiq.valor = formata_valor(payslip.total_folha)

                # Popula detPgtoFer.detRubrFer
                for line in payslip.line_ids:

                    # Somente pega as Rubricas de Retenção de IRRF e Pensão Alimentícia
                    if line.salary_rule_id.cod_inc_irrf_calculado in \
                            ['00', '01', '09', '13', '33', '43', '46', '53',
                             '63', '75', '93'] and line.total:

                        det_rubr_fer = pysped.esocial.leiaute.S1210_DetRubrFer_2()
                        det_rubr_fer.codRubr.valor = line.salary_rule_id.codigo
                        det_rubr_fer.ideTabRubr.valor = line.salary_rule_id.identificador
                        if line.quantity and float(line.quantity) != 1:
                            # det_rubr_fer.qtdRubr.valor = float(line.quantity)
                            det_rubr_fer.qtdRubr.valor = formata_valor(line.quantity)
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

        return S1210, validacao

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()

        if evento:
            for tot in evento.tot:

                if tot.tipo.valor == 'S5002':

                    # Busca o sped.registro que originou esse totalizador
                    sped_registro = self.env['sped.registro'].search([
                        ('registro', '=', 'S-1210'),
                        ('recibo', '=', tot.eSocial.evento.ideEvento.nrRecArqBase.valor)
                    ])

                    # Busca pelo sped.registro deste totalizador (se ele já existir)
                    sped_s5002 = self.env['sped.registro'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Busca pelo registro intermediário (se ele já existir)
                    sped_intermediario = self.env['sped.irrf'].search([
                        ('id_evento', '=', tot.eSocial.evento.Id.valor)
                    ])

                    # Popula os valores para criar/alterar o registro intermediário do totalizador
                    vals_intermediario_totalizador = {
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'periodo_id': sped_registro.origem_intermediario.periodo_id.id,
                        'trabalhador_id': sped_registro.origem_intermediario.beneficiario_id.id,
                        'sped_registro_s1210': sped_registro.id,
                    }
                    if tot.eSocial.evento.infoDep:
                        vals_intermediario_totalizador['vr_ded_deps'] = \
                            float(tot.eSocial.evento.infoDep[0].vrDedDep.valor)

                    # Cria/Altera o registro intermediário
                    if sped_intermediario:
                        sped_intermediario.write(vals_intermediario_totalizador)
                    else:
                        sped_intermediario = self.env['sped.irrf'].create(vals_intermediario_totalizador)

                    # Popula os valores para criar/alterar o sped.registro do totalizador
                    vals_registro_totalizador = {
                        'tipo': 'esocial',
                        'registro': 'S-5002',
                        'evento': 'evtIrrfBenef',
                        'operacao': 'na',
                        'ambiente': sped_registro.ambiente,
                        'origem': ('sped.irrf,%s' % sped_intermediario.id),
                        'origem_intermediario': ('sped.irrf,%s' % sped_intermediario.id),
                        'company_id': sped_registro.company_id.id,
                        'id_evento': tot.eSocial.evento.Id.valor,
                        'situacao': '4',
                        'recibo': tot.eSocial.evento.ideEvento.nrRecArqBase.valor,
                    }

                    # Cria/Altera o sped.registro do totalizador
                    if sped_s5002:
                        sped_s5002.write(vals_registro_totalizador)
                    else:
                        sped_s5002 = self.env['sped.registro'].create(vals_registro_totalizador)

                    # Popula o intermediário totalizador com o registro totalizador
                    sped_intermediario.sped_registro_s5002 = sped_s5002

                    # Popula o intermediário S1200 com o intermediário totalizador
                    self.s5002_id = sped_intermediario

                    # Popula o XML em anexo no sped.registro totalizador
                    if sped_s5002.consulta_xml_id:
                        consulta = sped_s5002.consulta_xml_id
                        sped_s5002.consulta_xml_id = False
                        consulta.unlink()
                    consulta_xml = tot.eSocial.xml
                    consulta_xml_nome = sped_s5002.id_evento + '-consulta.xml'
                    anexo_id = sped_registro._grava_anexo(consulta_xml_nome, consulta_xml)
                    sped_s5002.consulta_xml_id = anexo_id

                    # Limpa a tabela sped.irrf.infoirrf
                    for irrf in sped_intermediario.infoirrf_ids:
                        irrf.unlink()

                    # Popula a tabela sped.irrf.basesirrf com os valores apurados no S-5002
                    for irrf in tot.eSocial.evento.infoIrrf:
                        for base in irrf.basesIrrf:

                            vals = {
                                'parent_id': sped_intermediario.id,
                                'cod_categ': irrf.codCateg.valor,
                                'ind_res_br': irrf.indResBr.valor,
                                'tp_valor': str(int(base.tpValor.valor)).zfill(2),
                                'valor': float(base.valor.valor),
                            }
                            self.env['sped.irrf.basesirrf'].create(vals)

                    # Popula a tabela sped.irrf.infoirrf com os valores apurados no S-5002
                    for irrf in tot.eSocial.evento.infoIrrf:
                        for info in irrf.irrf:

                            vals = {
                                'parent_id': sped_intermediario.id,
                                'cod_categ': irrf.codCateg.valor,
                                'ind_res_br': irrf.indResBr.valor,
                                'tp_cr': info.tpCR.valor,
                                'vr_irrf_desc': float(info.vrIrrfDesc.valor),
                            }
                            self.env['sped.irrf.infoirrf'].create(vals)

                    # Adiciona o S-5002 ao Período do e-Social que gerou o S-1210 relacionado
                    periodo = self.env['sped.esocial'].search([
                        ('company_id', '=', self.company_id.id),
                        ('periodo_id', '=', self.periodo_id.id),
                    ])
                    periodo.irrf_trabalhador_ids = [(4, sped_intermediario.id)]

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()
        return self.beneficiario_id
