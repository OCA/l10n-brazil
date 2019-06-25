# -*- coding: utf-8 -*-
# Copyright (C) 2018 ABGF (http://www.abgf.gov.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import timedelta

from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    boletos_ids = fields.One2many(
        string='Guias/Boletos',
        comodel_name='financial.move',
        inverse_name='hr_payslip_run_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    def gerar_financial_move_darf(
            self, codigo_receita, valor, partner_id=False, num_referencia=False):
        '''
         Tratar dados do sefip e criar um dict para criar financial.move de
         guia DARF.
        :param DARF:  float com valor total do recolhimento
        :return: dict com valores para criar financial.move
        '''

        # Número do documento da DARF
        sequence_id = self.company_id.darf_sequence_id.id
        doc_number = str(self.env['ir.sequence'].next_by_id(sequence_id))

        # Definir quem sera o contribuinte da DARF, se nao passar nenhum
        # nos parametros assume que é a empresa
        if not partner_id:
            company_id = self.env['res.company'].search([
                ('eh_empresa_base', '=', True)
            ], limit=1)
            partner_id = company_id.partner_id

        # Preencher campo para indicar tipo de financial.move e tambem
        # preencher a data de vencimento
        descricao = 'DARF'

        if codigo_receita == '0588':
            descricao += ' - Diretores'

        if codigo_receita == '0561':
            descricao += ' - Funcionários'

        if codigo_receita == '1661':
            descricao += ' - PSS Plano de Seguridade Social'

        if codigo_receita == '1769':
            descricao += ' - PSS Patronal'

        # Calcular data de vencimento da DARF
        # data de vencimento setada na conf da empresa
        dia = str(self.company_id.darf_dia_vencimento)

        ano = self.ano

        # Guias para mes subsequente
        if self.mes_do_ano < 12:
            mes_do_ano = self.mes_do_ano + 1
        elif self.mes_do_ano >= 12:
            mes_do_ano = 1
            ano = self.ano + 1

        data = '{}-{:02d}-{}'.format(ano, mes_do_ano, dia)
        data_vencimento = \
            fields.Datetime.from_string(data + ' 03:00:00')

        # Código de DARFS de PSS
        codigo_receita_PSS = ['1769', '1661']

        # Se forem darfs de PSS, sera no primeiro dia
        if codigo_receita in codigo_receita_PSS:
            data_vencimento = data_vencimento.replace(day=1)

            # No caso de DARFS para PSS deverá ser no primeiro dia útil.
            # Caso dia 01 não seja útil, pegar o próximo
            while not self.company_id.default_resource_calendar_id. \
                    data_eh_dia_util(data_vencimento):
                data_vencimento += timedelta(days=1)

        # Antecipar data caso caia em feriado
        while not self.company_id.default_resource_calendar_id.\
                data_eh_dia_util(data_vencimento):
            data_vencimento -= timedelta(days=1)

        # Gerar FINANCEIRO da DARF
        vals_darf = {
            'date_document': fields.Date.today(),
            'partner_id': partner_id.id,
            'doc_source_id': 'hr.payslip.run,' + str(self.id),
            'company_id': self.company_id.id,
            'amount_document': valor,
            'document_number': 'DARF-' + str(doc_number),
            'account_id': self.company_id.darf_account_id.id,
            'document_type_id': self.company_id.darf_document_type.id,
            'type': '2pay',
            'date_maturity': data_vencimento,
            'payment_mode_id': self.company_id.darf_carteira_cobranca.id,
            'hr_payslip_run_id': self.id,
            'cod_receita': codigo_receita,
            'descricao': descricao,
            'num_referencia': num_referencia,
        }
        financial_move_darf = self.env['financial.move'].create(vals_darf)

        # Gerar PDF da DARF
        financial_move_darf.button_boleto()

        return financial_move_darf


    def gerar_financial_move_gps(self, empresa_id, dados_empresa):
        '''
         Criar financial.move de guia GPS, imprimir GPS e anexá-la ao move.
        :param GPS: float com valor total do recolhimento
        :return: financial.move
        '''

        empresa = self.env['res.company'].browse(empresa_id)

        sequence_id = empresa.darf_sequence_id.id
        doc_number = str(self.env['ir.sequence'].next_by_id(sequence_id))

        GPS = dados_empresa['INSS_funcionarios'] + \
              dados_empresa['INSS_empresa'] + \
              dados_empresa['INSS_outras_entidades'] + \
              dados_empresa['INSS_rat_fap']

        INSS = dados_empresa['INSS_funcionarios'] + \
               dados_empresa['INSS_empresa'] + \
               dados_empresa['INSS_rat_fap']

        TERCEIROS = dados_empresa['INSS_outras_entidades']

        descricao = 'GPS - '+ empresa.name

        # Gerar movimentação financeira do GPS
        vals_gps = {
            'date_document': fields.Date.today(),
            'partner_id': self.env.ref('base.user_root').id,
            'doc_source_id': 'hr.payslip.run,' + str(self.id),
            'company_id': empresa_id,
            'document_number': 'GPS-' + str(doc_number),
            'account_id': empresa.gps_account_id.id,
            'document_type_id': empresa.gps_document_type.id,
            'type': '2pay',
            'date_maturity': fields.Date.today(),
            'payment_mode_id': empresa.gps_carteira_cobranca.id,
            'hr_payslip_run_id': self.id,
            'valor_inss_terceiros': str(TERCEIROS),
            'valor_inss': str(INSS),
            'amount_document': GPS,
            'descricao': descricao,
        }
        financial_move_gps = self.env['financial.move'].create(vals_gps)

        # Gerar PDF DA GPS
        financial_move_gps.button_boleto()

        return financial_move_gps

    def gerar_guias_pagamento(self):
        """
        Gerar dicionarios contendo os valores das GUIAS
        :return:
        """
        empresas = {}
        guia_pss = []
        darfs = {}
        contribuicao_sindical = {}
        darf_analitico = []

        for holerite in self.slip_ids + self.payslip_rescisao_ids:
            if not empresas.get(holerite.company_id.id):
                empresas.update({
                    holerite.company_id.id: {
                        'INSS_funcionarios': 0.00,
                        'INSS_empresa': 0.00,
                        'INSS_outras_entidades': 0.00,
                        'INSS_rat_fap': 0.00,
                    }
                })

            for line in holerite.line_ids:
                remuneracao = line.slip_id.line_ids.filtered(
                    lambda x: x.code == 'LIQUIDO')
                if line.code == 'CONTRIBUICAO_SINDICAL':
                    id_sindicato = \
                        line.slip_id.contract_id.partner_union.id or 0
                    if id_sindicato in contribuicao_sindical:
                        contribuicao_sindical[id_sindicato][
                            'contribuicao_sindicato'] += line.total
                        contribuicao_sindical[id_sindicato][
                            'qtd_contribuintes'] += 1
                        contribuicao_sindical[id_sindicato][
                            'total_remuneracao'] += remuneracao.total
                    else:
                        contribuicao_sindical[id_sindicato] = {}
                        contribuicao_sindical[id_sindicato][
                            'contribuicao_sindicato'] = line.total
                        contribuicao_sindical[id_sindicato][
                            'qtd_contribuintes'] = 1
                        contribuicao_sindical[id_sindicato][
                            'total_remuneracao'] = remuneracao.total
                elif line.code in ['INSS', 'INSS_13', 'INSS_FERIAS_DA_COMPETENCIA']:
                    empresas[line.slip_id.company_id.id][
                        'INSS_funcionarios'] += line.total
                elif line.code == 'INSS_EMPRESA':
                    empresas[line.slip_id.company_id.id][
                        'INSS_empresa'] += line.total
                elif line.code == 'INSS_OUTRAS_ENTIDADES':
                    empresas[line.slip_id.company_id.id][
                        'INSS_outras_entidades'] += line.total
                elif line.code == 'INSS_RAT_FAP':
                    empresas[line.slip_id.company_id.id][
                        'INSS_rat_fap'] += line.total

                #
                # GERAR DARF
                #
                # Para rubricas de PSS patronal
                elif line.code in ['PSS_PATRONAL', 'PSS_13_PATRONAL', 'PSS_PATRONAL_MES_ANTERIOR']:
                    guia_pss.append({
                        'code': '1769',
                        'valor': line.total,
                        'partner_id': line.employee_id.company_id.partner_id,
                        'num_referencia':
                            line.employee_id.address_home_id.cnpj_cpf,
                    })

                # Para rubricas de PSS do funcionario
                elif line.code in ['PSS', 'PSS_13', 'PSS_MES_ANT']:
                    guia_pss.append({
                        'code': '1661',
                        'valor': line.total,
                        'partner_id': line.employee_id.address_home_id,
                        'num_referencia': '',
                    })

                # para gerar a DARF, identificar a categoria de contrato pois
                # cada categoria tem um código de emissao diferente
                elif line.code in ['IRPF', 'IRPF_13', 'IRPF_FERIAS',
                                   'IRPF_FERIAS_FERIAS',
                                   'IRRF_13_SALARIO_ESPECIFICA']:

                    codigo_darf = line.slip_id.contract_id.codigo_guia_darf

                    if darfs.get(codigo_darf):
                        darfs[codigo_darf] += line.total
                    else:
                        darfs.update({
                            codigo_darf: line.total
                        })

                    if 'FERIAS' in line.code:
                        base = 0.00
                    else:
                        base = line.slip_id.line_ids.filtered(
                            lambda x: x.code == 'BASE_IRPF').total

                    darf_analitico.append({
                        'nome': line.slip_id.contract_id.display_name,
                        'company_id': line.slip_id.contract_id.company_id.id,
                        'code': line.code,
                        'codigo_darf': codigo_darf,
                        'valor': line.total,
                        'base': base or 0.0,
                    })

        return empresas, darfs, contribuicao_sindical, guia_pss, darf_analitico

    @api.multi
    def gerar_boletos(self):
        '''
        Criar ordem de pagamento para boleto de sindicato
        1. Configurar os dados para criação das financial.moves
        2. Criar os financial.moves
        '''
        #
        # Excluir registros financeiros anteriores
        #
        for boleto_id in self.boletos_ids:
            boleto_id.unlink()

        for record in self:

            created_ids = []

            empresas, darfs, contribuicao_sindical, pss, darf_analitico = \
                self.gerar_guias_pagamento()

            for company in empresas:
                dados_empresa = empresas[company]
                financial_move_gps = self.gerar_financial_move_gps(
                    company, dados_empresa)
                created_ids.append(financial_move_gps.id)

            for cod_darf in darfs:
                financial_move_darf = \
                    self.gerar_financial_move_darf(cod_darf, darfs[cod_darf])
                created_ids.append(financial_move_darf.id)

            for sindicato in contribuicao_sindical:
                vals = self.prepara_financial_move(
                    sindicato, contribuicao_sindical[sindicato])
                financial_move = self.env['financial.move'].create(vals)
                created_ids.append(financial_move.id)

            for guia_pss in pss:
                financial_move_darf = self.gerar_financial_move_darf(
                    guia_pss.get('code'), guia_pss.get('valor'),
                    guia_pss.get('partner_id'), guia_pss.get('num_referencia'))
                created_ids.append(financial_move_darf.id)

            return {
                'domain': "[('id', 'in', %s)]" % created_ids,
                'name': _("Guias geradas"),
                'res_ids': created_ids,
                'view_type': 'form',
                'view_mode': 'tree,form',
                'auto_search': True,
                'res_model': 'financial.move',
                'view_id': False,
                'search_view_id': False,
                'type': 'ir.actions.act_window'
            }
