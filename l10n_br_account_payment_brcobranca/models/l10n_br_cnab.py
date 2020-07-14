# -*- coding: utf-8 -*-
# Copyright 2017 Akretion - Renato Lima <renato.lima@akretion.com.br>
# Copyright 2017 Akretion - Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import requests
import json
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError

DICT_OCORRENCIAS_BRADESCO = {
    '02': u'Entrada Confirmada (verificar motivo na posição 319 a 328)',
    '03': u'Entrada Rejeitada ( verificar motivo na posição 319 a 328)',
    '06': u'Liquidação normal (sem motivo)',
    '09': u'Baixado Automat. via Arquivo (verificar motivo posição 319 a 328)',
    '10': u'Baixado conforme instruções da Agência('
          u'verificar motivo pos.319 a 328)',
    '11': u'Em Ser - Arquivo de Títulos pendentes (sem motivo)',
    '12': u'Abatimento Concedido (sem motivo)',
    '13': u'Abatimento Cancelado (sem motivo)',
    '14': u'Vencimento Alterado (sem motivo)',
    '15': u'Liquidação em Cartório (sem motivo)',
    '16': u'Título Pago em Cheque – Vinculado',
    '17': u'Liquidação após baixa ou Título não registrado (sem motivo)',
    '18': u'Acerto de Depositária (sem motivo)',
    '19': u'Confirmação Receb. Inst. de Protesto '
          u'(verificar motivo pos.295 a 295)',
    '20': u'Confirmação Recebimento Instrução Sustação de'
          u' Protesto (sem motivo)',
    '21': u'Acerto do Controle do Participante (sem motivo)',
    '22': u'Título Com Pagamento Cancelado',
    '23': u'Entrada do Título em Cartório (sem motivo)',
    '24': u'Entrada rejeitada por CEP Irregular'
          u' (verificar motivo pos.319 a 328)',
    '25': u'Confirmação Receb.Inst.de Protesto Falimentar'
          u' (verificar pos.295 a 295)',
    '27': u'Baixa Rejeitada (verificar motivo posição 319 a 328)',
    '28': u'Débito de tarifas/custas (verificar motivo na posição 319 a 328)',
    '29': u'Ocorrências do Pagador (NOVO)',
    '30': u'Alteração de Outros Dados Rejeitados '
          u'(verificar motivo pos.319 a 328)',
    '32': u'Instrução Rejeitada (verificar motivo posição 319 a 328)',
    '33': u'Confirmação Pedido Alteração Outros Dados (sem motivo)',
    '34': u'Retirado de Cartório e Manutenção Carteira (sem motivo)',
    '35': u'Desagendamento do débito automático '
          u'(verificar motivos pos. 319 a 328)',
    '40': u'Estorno de pagamento (NOVO)',
    '55': u'Sustado judicial (NOVO)',
    '68': u'Acerto dos dados do rateio de Crédito (verificar motivo posição de'
          u' status do registro tipo 3)',
    '69': u'Cancelamento dos dados do rateio (verificar motivo posição de'
          u' status do registro tipo 3)',
    '073': u'Confirmação Receb. Pedido de Negativação (NOVO)',
    '074': u'Confir Pedido de Excl de Negat (com ou sem baixa) (NOVO)',
    '00': u'Nota: Para as ocorrências sem motivos, as posições serão'
          u' informadas com Zeros.',
}

DICT_OCORRENCIAS_ITAU = {
    '02': u'ENTRADA CONFIRMADA COM POSSIBILIDADE DE MENSAGEM'
          u' (NOTA 20 – TABELA 10)',
    '03': u'ENTRADA REJEITADA (NOTA 20 – TABELA 1)',
    '04': u'ALTERAÇÃO DE DADOS – NOVA ENTRADA OU ALTERAÇÃO/EXCLUSÃO'
          u' DE DADOS ACATADA',
    '05': u'ALTERAÇÃO DE DADOS – BAIXA',
    '06': u'LIQUIDAÇÃO NORMAL',
    '07': u'LIQUIDAÇÃO PARCIAL – COBRANÇA INTELIGENTE (B2B)',
    '08': u'LIQUIDAÇÃO EM CARTÓRIO',
    '09': u'BAIXA SIMPLES',
    '10': u'BAIXA POR TER SIDO LIQUIDADO',
    '11': u'EM SER (SÓ NO RETORNO MENSAL)',
    '12': u'ABATIMENTO CONCEDIDO',
    '13': u'ABATIMENTO CANCELADO',
    '14': u'VENCIMENTO ALTERADO',
    '15': u'BAIXAS REJEITADAS (NOTA 20 – TABELA 4)',
    '16': u'INSTRUÇÕES REJEITADAS (NOTA 20 – TABELA 3)',
    '17': u'ALTERAÇÃO/EXCLUSÃO DE DADOS REJEITADOS (NOTA 20 – TABELA 2)',
    '18': u'COBRANÇA CONTRATUAL – INSTRUÇÕES/ALTERAÇÕES'
          u' REJEITADAS/PENDENTES (NOTA 20 – TABELA 5)',
    '19': u'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE PROTESTO',
    '20': u'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE SUSTAÇÃO'
          u' DE PROTESTO /TARIFA',
    '21': u'CONFIRMA RECEBIMENTO DE INSTRUÇÃO DE NÃO PROTESTAR',
    '23': u'TÍTULO ENVIADO A CARTÓRIO/TARIFA',
    '24': u'INSTRUÇÃO DE PROTESTO REJEITADA / SUSTADA / PENDENTE'
          u' (NOTA 20 – TABELA 7)',
    '25': u'ALEGAÇÕES DO PAGADOR (NOTA 20 – TABELA 6)',
    '26': u'TARIFA DE AVISO DE COBRANÇA',
    '27': u'TARIFA DE EXTRATO POSIÇÃO (B40X)',
    '28': u'TARIFA DE RELAÇÃO DAS LIQUIDAÇÕES',
    '29': u'TARIFA DE MANUTENÇÃO DE TÍTULOS VENCIDOS',
    '30': u'DÉBITO MENSAL DE TARIFAS (PARA ENTRADAS E BAIXAS)',
    '32': u'BAIXA POR TER SIDO PROTESTADO',
    '33': u'CUSTAS DE PROTESTO',
    '34': u'CUSTAS DE SUSTAÇÃO',
    '35': u'CUSTAS DE CARTÓRIO DISTRIBUIDOR',
    '36': u'CUSTAS DE EDITAL',
    '37': u'TARIFA DE EMISSÃO DE BOLETO/TARIFA DE ENVIO DE DUPLICATA',
    '38': u'TARIFA DE INSTRUÇÃO',
    '39': u'TARIFA DE OCORRÊNCIAS',
    '40': u'TARIFA MENSAL DE EMISSÃO DE BOLETO/TARIFA MENSAL'
          u' DE ENVIO DE DUPLICATA',
    '41': u'DÉBITO MENSAL DE TARIFAS – EXTRATO DE POSIÇÃO (B4EP/B4OX)',
    '42': u'DÉBITO MENSAL DE TARIFAS – OUTRAS INSTRUÇÕES',
    '43': u'DÉBITO MENSAL DE TARIFAS – MANUTENÇÃO DE TÍTULOS VENCIDOS',
    '44': u'DÉBITO MENSAL DE TARIFAS – OUTRAS OCORRÊNCIAS',
    '45': u'DÉBITO MENSAL DE TARIFAS – PROTESTO',
    '46': u'DÉBITO MENSAL DE TARIFAS – SUSTAÇÃO DE PROTESTO',
    '47': u'BAIXA COM TRANSFERÊNCIA PARA DESCONTO',
    '48': u'CUSTAS DE SUSTAÇÃO JUDICIAL',
    '51': u'TARIFA MENSAL REF A ENTRADAS BANCOS CORRESPONDENTES NA CARTEIRA',
    '52': u'TARIFA MENSAL BAIXAS NA CARTEIRA',
    '53': u'TARIFA MENSAL BAIXAS EM BANCOS CORRESPONDENTES NA CARTEIRA',
    '54': u'TARIFA MENSAL DE LIQUIDAÇÕES NA CARTEIRA',
    '55': u'TARIFA MENSAL DE LIQUIDAÇÕES EM BANCOS'
          u' CORRESPONDENTES NA CARTEIRA',
    '56': u'CUSTAS DE IRREGULARIDADE',
    '57': u'INSTRUÇÃO CANCELADA (NOTA 20 – TABELA 8)',
    '59': u'BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG',
    '60': u'ENTRADA REJEITADA CARNÊ (NOTA 20 – TABELA 1)',
    '61': u'TARIFA EMISSÃO AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)',
    '62': u'DÉBITO MENSAL DE TARIFA – AVISO DE MOVIMENTAÇÃO DE TÍTULOS (2154)',
    '63': u'TÍTULO SUSTADO JUDICIALMENTE',
    '64': u'ENTRADA CONFIRMADA COM RATEIO DE CRÉDITO',
    '65': u'PAGAMENTO COM CHEQUE – AGUARDANDO COMPENSAÇÃO',
    '69': u'CHEQUE DEVOLVIDO (NOTA 20 – TABELA 9)',
    '71': u'ENTRADA REGISTRADA, AGUARDANDO AVALIAÇÃO',
    '72': u'BAIXA POR CRÉDITO EM C/C ATRAVÉS DO SISPAG'
          u' SEM TÍTULO CORRESPONDENTE',
    '73': u'CONFIRMAÇÃO DE ENTRADA NA COBRANÇA SIMPLES –'
          u' ENTRADA NÃO ACEITA NA COBRANÇA CONTRATUAL',
    '74': u'INSTRUÇÃO DE NEGATIVAÇÃO EXPRESSA REJEITADA (NOTA 20 – TABELA 11)',
    '75': u'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE ENTRADA'
          u' EM NEGATIVAÇÃO EXPRESSA',
    '76': u'CHEQUE COMPENSADO',
    '77': u'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE EXCLUSÃO DE'
          u' ENTRADA EM NEGATIVAÇÃO EXPRESSA',
    '78': u'CONFIRMAÇÃO DE RECEBIMENTO DE INSTRUÇÃO DE CANCELAMENTO DE'
          u' NEGATIVAÇÃO EXPRESSA',
    '79': u'NEGATIVAÇÃO EXPRESSA INFORMACIONAL (NOTA 20 – TABELA 12)',
    '80': u'CONFIRMAÇÃO DE ENTRADA EM NEGATIVAÇÃO EXPRESSA – TARIFA',
    '82': u'CONFIRMAÇÃO DO CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA – TARIFA',
    '83': u'CONFIRMAÇÃO DE EXCLUSÃO DE ENTRADA EM NEGATIVAÇÃO'
          u' EXPRESSA POR LIQUIDAÇÃO – TARIFA',
    '85': u'TARIFA POR BOLETO (ATÉ 03 ENVIOS) COBRANÇA ATIVA ELETRÔNICA',
    '86': u'TARIFA EMAIL COBRANÇA ATIVA ELETRÔNICA',
    '87': u'TARIFA SMS COBRANÇA ATIVA ELETRÔNICA',
    '88': u'TARIFA MENSAL POR BOLETO (ATÉ 03 ENVIOS)'
          u' COBRANÇA ATIVA ELETRÔNICA',
    '89': u'TARIFA MENSAL EMAIL COBRANÇA ATIVA ELETRÔNICA',
    '90': u'TARIFA MENSAL SMS COBRANÇA ATIVA ELETRÔNICA',
    '91': u'TARIFA MENSAL DE EXCLUSÃO DE ENTRADA DE NEGATIVAÇÃO EXPRESSA',
    '92': u'TARIFA MENSAL DE CANCELAMENTO DE NEGATIVAÇÃO EXPRESSA',
    '93': u'TARIFA MENSAL DE EXCLUSÃO DE NEGATIVAÇÃO EXPRESSA POR LIQUIDAÇÃO',
}

DICT_OCORRENCIAS_UNICRED = {
    '01': '01 - Pago (Título protestado pago em cartório)',
    '02': '02 - Instrução Confirmada*',
    '03': '03 - Instrução Rejeitada*',
    '04': '04 - Sustado Judicial (Título protestado sustado judicialmente)',
    '06': '06 - Liquidação Normal *',
    '07': '07 - Liquidação em Condicional (Título liquidado em cartório com'
          ' cheque do próprio devedor)',
    '08': '08 - Sustado Definitivo (Título protestado sustado judicialmente)',
    '09': '09 - Liquidação de Título Descontado',
    '10': '10 - Protesto solicitado',
    '11': '11 - Protesto Em cartório',
    '12': '12 - Sustação solicitada'
}


class L10nBrHrCnab(models.Model):
    _inherit = "l10n_br.cnab"

    account_journal = fields.Many2one(
        'account.journal', 'Journal used in Bank Statement',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Journal used in create of Bank Statement.'
    )
    cnab_type = fields.Selection(
        [('cnab400', u'CNAB 400')], 'CNAB Type File',
        default='cnab400',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    bank = fields.Selection(
        [('bradesco', 'Bradesco'),
         ('itau', 'Itaú'),
         ('unicred', 'Unicred')],
        string='Bank', states={'draft': [('readonly', False)]}
    )

    @api.multi
    def processar_arquivo_retorno(self):

        files = {'data': base64.b64decode(self.arquivo_retorno)}
        api_address = self.env[
            "ir.config_parameter"].sudo().get_param(
            "l10n_br_account_payment_brcobranca.boleto_cnab_api")
        if not api_address:
            raise UserError(
                ('Não é possível gerar o retorno.\n'
                 'Informe o Endereço IP ou Nome do'
                 ' Boleto CNAB API.'))
        # Ex.: "http://boleto_cnab_api:9292/api/retorno"
        api_service_address = \
            'http://' + api_address + ':9292/api/retorno'
        res = requests.post(
            api_service_address,
            data={
                'type': self.cnab_type,
                'bank': self.bank,
            }, files=files)

        if res.status_code != 201:
            raise UserError(res.text)

        string_result = res.json()
        data = json.loads(string_result)

        self.processar_arquivo_retorno_cnab400(data)

    @api.multi
    def processar_arquivo_retorno_cnab400(self, data):

        lote_id = self.env['l10n_br.cnab.lote'].create({'cnab_id': self.id})

        quantidade_registros = 0
        total_valores = 0
        balance_end_real = 0.0
        line_statement_vals = []
        reconcile_statement_vals = []

        for dict_line in data:
            if int(dict_line['codigo_registro']) != 1:
                # Bradesco
                # Existe o codigo de registro 9 que eh um totalizador
                # porem os campos estao colocados em outras posicoes
                # que nao estao mapeadas no BRCobranca
                # Itau
                # 9 - Registro Trailer do Arquivo
                # 4 e 5 - Registro de Detalhe (Opcional)
                continue

            # Nosso Numero sem o Digito Verificador
            if self.bank == 'bradesco':
                account_move_line = self.env['account.move.line'].search(
                    [('nosso_numero', '=', dict_line['nosso_numero'][:11])]
                )
            elif self.bank == 'unicred':
                account_move_line = self.env['account.move.line'].search(
                    [('nosso_numero', '=', dict_line['nosso_numero'][6:16])]
                )

            payment_line = self.env['account.payment.line'].search(
                [('move_line_id', '=', account_move_line.id)]
            )

            valor_titulo = float(
                str(dict_line['valor_titulo'][0:11] + '.' +
                    dict_line['valor_titulo'][11:]))

            total_valores += valor_titulo

            data_ocorrencia = datetime.date.today()
            # Cada Banco pode possuir um Codigo de Ocorrencia distinto
            if self.bank == 'bradesco':
                if (dict_line['data_ocorrencia'] == '000000' or
                        not dict_line['data_ocorrencia']):
                    data_ocorrencia = dict_line['data_de_ocorrencia']
                else:
                    data_ocorrencia = datetime.datetime.strptime(
                        str(dict_line['data_ocorrencia']), "%d%m%y").date()
                descricao_ocorrencia = DICT_OCORRENCIAS_BRADESCO[
                       dict_line['codigo_ocorrencia']].encode('utf-8')

            if self.bank == 'itau':
                descricao_ocorrencia = DICT_OCORRENCIAS_ITAU[
                       dict_line['codigo_ocorrencia']].encode('utf-8')

            if self.bank == 'unicred':
                descricao_ocorrencia = DICT_OCORRENCIAS_UNICRED[
                       dict_line['codigo_ocorrencia']].encode('utf-8')

            # Linha não encontrada
            if not account_move_line:
                vals_evento = {
                   'lote_id': lote_id.id,
                   'ocorrencias': descricao_ocorrencia,
                   'data_ocorrencia': data_ocorrencia,
                   'str_motiv_a':
                       u' * - BOLETO NÃO ENCONTRADO DENTRO DO PROGRAMA',
                   'nosso_numero': dict_line['nosso_numero'],
                   'seu_numero': dict_line['documento_numero'],
                   'valor_titulo': valor_titulo,
                }
                self.env['l10n_br.cnab.evento'].create(vals_evento)
                continue

            valor_recebido = 0.0
            if dict_line['valor_recebido']:
                valor_recebido = float(
                    str(dict_line['valor_recebido'][0:11] + '.' +
                        dict_line['valor_recebido'][11:]))

            if (dict_line['data_credito'] == '000000' or
                    not dict_line['data_credito']):
                data_credito = dict_line['data_credito']
            else:
                data_credito = datetime.datetime.strptime(
                    str(dict_line['data_credito']), "%d%m%y").date()

            if (str(dict_line['codigo_ocorrencia']) in ('06', '17')
                    and self.bank == 'bradesco') or (
                        str(dict_line['codigo_ocorrencia']) in ('06', '10') and
                        self.bank == 'itau') or (
                        str(dict_line['codigo_ocorrencia']) in
                        ('01', '06', '07', '09') and
                        self.bank == 'unicred'):

                reconcile_line_vals = {
                    'numero_documento': account_move_line.numero_documento}
                counterpart_line_vals = []
                new_aml_vals = []

                vals_evento = {
                    'lote_id': lote_id.id,
                    'data_ocorrencia': data_ocorrencia,
                    'data_real_pagamento': data_credito.strftime("%Y-%m-%d"),
                    # 'segmento': evento.servico_segmento,
                    # 'favorecido_nome':
                    #    obj_account_move_line.company_id.partner_id.name,
                    'favorecido_conta_bancaria_id':
                        account_move_line.payment_mode_id.
                        fixed_journal_id.bank_account_id.id,
                    'nosso_numero': dict_line['nosso_numero'],
                    'identificacao_titulo_empresa':
                        dict_line['documento_numero'] or
                        account_move_line.numero_documento,
                    # 'tipo_moeda': evento.credito_moeda_tipo,
                    'valor': valor_titulo,
                    'valor_pagamento': valor_recebido,
                    'ocorrencias': descricao_ocorrencia,
                    'bank_payment_line_id':
                        payment_line.bank_line_id.id or False,
                    'invoice_id': account_move_line.invoice_id.id,
                    'data_vencimento': datetime.datetime.strptime(
                        str(dict_line['data_vencimento']), "%d%m%y").date(),
                }

                # Valor Desconto
                if dict_line.get('desconto'):
                    valor_desconto = float(
                        str(dict_line['desconto'][0:11] + '.' +
                            dict_line['desconto'][11:]))
                    vals_evento['valor_desconto'] = valor_desconto

                    # Atualiza o Valor Recebido
                    valor_recebido -= valor_desconto

                    new_aml_vals.append({
                        'name': 'Desconto (boleto)',
                        'debit': valor_desconto,
                        'credit': 0.0,
                        # TODO - Definir Conta Contabil de Desconto
                        'account_id': account_move_line.payment_mode_id.
                            default_tax_account_id.id,
                    })

                # Valor Juros Mora - valor de mora e multa pagos pelo sacado
                if dict_line.get('juros_mora'):
                    valor_juros_mora = float(
                        str(dict_line['juros_mora'][0:11] + '.' +
                            dict_line['juros_mora'][11:]))

                    vals_evento['juros_mora_multa'] = valor_juros_mora

                    # Atualiza o Valor Recebido
                    valor_recebido += valor_juros_mora

                    new_aml_vals.append({
                        'name': 'Valor Juros Mora (boleto)',
                        'debit': 0.0,
                        'credit': valor_juros_mora,
                        # TODO - Definir Conta Contábil de Juros Mora e Multa
                        'account_id': account_move_line.payment_mode_id.
                        fixed_journal_id.default_credit_account_id.id,
                    })

                # Valor Tarifa
                if dict_line.get('valor_tarifa'):
                    valor_tarifa = float(
                        str(dict_line['valor_tarifa'][0:4] + '.' +
                            dict_line['valor_tarifa'][4:]))
                    vals_evento['tarifa_cobranca'] = valor_tarifa

                    # Atualiza o Valor Recebido
                    valor_recebido -= valor_tarifa

                    new_aml_vals.append({
                        'name': 'Tarifas bancárias (boleto)',
                        'debit': valor_tarifa,
                        'credit': 0.0,
                        'account_id': account_move_line.payment_mode_id.
                            default_tax_account_id.id,
                    })

                # Valor Abatimento
                if dict_line.get('valor_abatimento'):
                    valor_abatimento = float(
                        str(dict_line['valor_abatimento'][0:11] + '.' +
                            dict_line['valor_abatimento'][11:]))
                    vals_evento['valor_abatimento'] = valor_abatimento

                    # Atualiza o valor recebido
                    valor_recebido -= valor_abatimento

                    new_aml_vals.append({
                        'name': 'Abatimento (boleto)',
                        'debit': valor_abatimento,
                        'credit': 0.0,
                        # TODO - Definir Conta Contabil de Abatimento
                        'account_id': account_move_line.payment_mode_id.
                        default_tax_account_id.id,
                    })

                # Monta o dicionario que sera usado
                # para criar o Extrato Bancario
                balance_end_real += valor_recebido
                line_statement_vals.append({
                    'name': account_move_line.numero_documento or '?',
                    'amount': valor_recebido,
                    'partner_id': account_move_line.partner_id.id,
                    'ref': account_move_line.ref,
                    'date': account_move_line.date,
                    'amount_currency': valor_recebido,
                    'currency_id': account_move_line.currency_id.id,
                })

                # Linha da Fatura a ser reconciliada
                counterpart_line_vals.append({
                    'name': account_move_line.numero_documento,
                    'debit': 0.0,
                    'credit': valor_titulo,
                    'move_line': account_move_line,
                })

                # Monta uma Lista com Dicionarios usados para
                # reconciliar o extrato bancario
                reconcile_line_vals['new_aml_vals'] = new_aml_vals
                reconcile_line_vals['counterpart_aml_vals'] = counterpart_line_vals
                reconcile_statement_vals.append(reconcile_line_vals)

            else:
                vals_evento = {
                    'lote_id': lote_id.id,
                    'ocorrencias': descricao_ocorrencia,
                    'data_ocorrencia': data_ocorrencia,
                    'nosso_numero': dict_line['nosso_numero'],
                    'seu_numero': account_move_line.numero_documento,
                    'valor_titulo': valor_titulo,
                }

            self.env['l10n_br.cnab.evento'].create(vals_evento)

        lote_id.total_valores = total_valores
        lote_id.qtd_registros = quantidade_registros
        self.num_lotes = 1
        self.num_eventos = quantidade_registros

        # Criacao de um Extrato Bancario a ser conciliado logo abaixo, sendo
        # necessário o usuario apenas clicar em Validar na tela do Extrato.
        # TODO - automatizar validando o extrato ou deixar de usar o extrato ?
        if line_statement_vals:
            vals_bank_statement = {
                # TODO - name of Bank Statement
                # 'name': 'BNK/%s/0001' % time.strftime('%Y'),
                'journal_id': self.account_journal.id,
                'balance_end_real': balance_end_real,
            }
            statement = self.env[
                'account.bank.statement'].create(vals_bank_statement)
            statement_line_obj = self.env['account.bank.statement.line']
            for line in line_statement_vals:
                line['statement_id'] = statement.id
                statement_line_obj.create(line)

        # Reconciliação do Extrato e Fatura
        for line in statement.line_ids:
            for reconcile_line in reconcile_statement_vals:
                if line.name == reconcile_line.get('numero_documento'):
                    line.process_reconciliation(
                         counterpart_aml_dicts=reconcile_line.get(
                             'counterpart_aml_vals'),
                         new_aml_dicts=reconcile_line.get(
                             'new_aml_vals')
                    )

        return self.write({'state': 'done'})


class L10nBrHrCnabEvento(models.Model):
    _inherit = "l10n_br.cnab.evento"

    data_ocorrencia = fields.Date(string=u"Data da Ocorrência")
    valor_titulo = fields.Float(string=u"Valor do Título")
