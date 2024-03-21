# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import requests
import json

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError

from odoo.addons.account_move_base_import.parser.file_parser import (
    FileParser,
    float_or_zero,
)

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

dict_brcobranca_bank = {
    '001': 'banco_brasil',
    '041': 'banrisul',
    '237': 'bradesco',
    '104': 'caixa',
    '399': 'hsbc',
    '341': 'itau',
    '033': 'santander',
    '748': 'sicred',
    '004': 'banco_nordeste',
    '021': 'banestes',
    '756': 'sicoob',
    '136': 'unicred',
}


class CNABFileParser(FileParser):
    """CNAB parser that use a define format in CNAB to import
    bank statement.
    """

    def __init__(self, journal, *args, **kwargs):
        # The name of the parser as it will be called
        self.parser_name = journal.import_type
        # The result as a list of row. One row per line of data in the file,
        # but not the commission one!
        self.result_row_list = None
        # The file buffer on which to work on
        self.filebuffer = None
        # The profile record to access its parameters in any parser method
        self.journal = journal
        self.move_date = None
        self.move_name = None
        self.move_ref = None
        self.support_multi_moves = None
        self.env = journal.env
        self.bank = self.journal.bank_account_id.bank_id

    @classmethod
    def parser_for(cls, parser_name):
        if parser_name == "cnab400":
            return parser_name == "cnab400"
        elif parser_name == "cnab240":
            return parser_name == "cnab240"

    def parse(self, filebuffer):

        files = {'data': base64.b64decode(filebuffer)}

        api_address = self.env[
            "ir.config_parameter"].sudo().get_param(
            "l10n_br_account_payment_brcobranca.boleto_cnab_api")
        if not api_address:
            raise UserError(
                ('Não é possível gerar o retorno.\n'
                 'Informe o Endereço IP ou Nome do'
                 ' Boleto CNAB API.'))
        # Ex.: "http://boleto_cnab_api:9292/api/retorno"
        bank_name_brcobranca = \
            dict_brcobranca_bank[self.bank.code_bc]
        api_service_address = \
            'http://' + api_address + ':9292/api/retorno'
        res = requests.post(
            api_service_address,
            data={
                'type': self.journal.import_type,
                'bank': bank_name_brcobranca,
            }, files=files)

        if res.status_code != 201:
            raise UserError(res.text)

        string_result = res.json()
        data = json.loads(string_result)

        self.result_row_list = self.processar_arquivo_retorno_cnab400(data)

        yield self.result_row_list

    @api.multi
    def processar_arquivo_retorno_cnab400(self, data):

        quantidade_registros = 0
        total_valores = 0
        balance_end_real = 0.0
        line_statement_vals = []

        # Forma de Lançamento do Retorno
        # Manual - Criação de uma Entrada de Diário com os valores de
        #          desconto, juros/mora, tarifa bancaria e abatimento
        #          e um Extrato Bancario com o valor total ( valor
        #          liquido + desconto + tarifa bancaria + abatimanto )
        # Automatico - Criação de uma Entrada de Diário com os valores
        #              da forma Manual mais o valor total, conciliado com
        #              a Fatura correspondente
        #
        cnab_return_method = self.env[
            'ir.config_parameter'].sudo().get_param(
            'l10n_br_account_payment_brcobranca.cnab_return_method')

        # Lista com os dados q poderão ser usados na criação das account move line
        result_row_list = []

        for linha_cnab in data:
            cnab = self.env['l10n_br.cnab'].create(vals={})
            lote_id = self.env['l10n_br.cnab.lote'].create({'cnab_id': cnab.id})

            if int(linha_cnab['codigo_registro']) != 1:
                # Bradesco
                # Existe o codigo de registro 9 que eh um totalizador
                # porem os campos estao colocados em outras posicoes
                # que nao estao mapeadas no BRCobranca
                # Itau
                # 9 - Registro Trailer do Arquivo
                # 4 e 5 - Registro de Detalhe (Opcional)
                # continue
                continue

            bank_name_brcobranca = \
                dict_brcobranca_bank[self.bank.code_bc]

            # Nosso Numero sem o Digito Verificador
            if bank_name_brcobranca == 'bradesco':
                account_move_line = self.env['account.move.line'].search(
                    [('own_number', '=', linha_cnab['nosso_numero'][:11])]
                )
            elif bank_name_brcobranca == 'unicred':
                account_move_line = self.env['account.move.line'].search(
                    [('own_number', '=', linha_cnab['nosso_numero'][6:16])]
                )

            payment_line = self.env['account.payment.line'].search(
                [('move_line_id', '=', account_move_line.id)]
            )

            valor_titulo = self.cnab_str_to_float(
                linha_cnab['valor_titulo'])

            total_valores += valor_titulo

            data_ocorrencia = datetime.date.today()
            cod_ocorrencia = str(linha_cnab['codigo_ocorrencia'])
            # Cada Banco pode possuir um Codigo de Ocorrencia distinto
            if bank_name_brcobranca == 'bradesco':
                if (linha_cnab['data_ocorrencia'] == '000000' or
                        not linha_cnab['data_ocorrencia']):
                    data_ocorrencia = linha_cnab['data_de_ocorrencia']
                else:
                    data_ocorrencia = datetime.datetime.strptime(
                        str(linha_cnab['data_ocorrencia']), "%d%m%y").date()
                descricao_ocorrencia = DICT_OCORRENCIAS_BRADESCO[
                    cod_ocorrencia].encode('utf-8')

            if bank_name_brcobranca == 'itau':
                descricao_ocorrencia = DICT_OCORRENCIAS_ITAU[
                    cod_ocorrencia].encode('utf-8')

            if bank_name_brcobranca == 'unicred':
                descricao_ocorrencia = DICT_OCORRENCIAS_UNICRED[
                    cod_ocorrencia].encode('utf-8')

            # Linha não encontrada
            if not account_move_line:
                vals_evento = {
                    'lote_id': lote_id.id,
                    'ocorrencias': descricao_ocorrencia,
                    'data_ocorrencia': data_ocorrencia,
                    'str_motiv_a':
                        u' * - BOLETO NÃO ENCONTRADO.',
                    'nosso_numero': linha_cnab['nosso_numero'],
                    'seu_numero': linha_cnab['documento_numero'],
                    'valor': valor_titulo,
                }
                self.env['l10n_br.cnab.evento'].create(vals_evento)
                continue

            valor_recebido = 0.0
            if linha_cnab['valor_recebido']:
                valor_recebido = self.cnab_str_to_float(
                    linha_cnab['valor_recebido'])

            if (linha_cnab['data_credito'] == '000000' or
                    not linha_cnab['data_credito']):
                data_credito = linha_cnab['data_credito']
            else:
                data_credito = datetime.datetime.strptime(
                    str(linha_cnab['data_credito']), "%d%m%y").date()

            # Codigos de Ocorrencia - Liquidação
            # TODO - esses codigos deveriam ser informados em um campo ao inves
            #  de estarem chumbados aqui
            if ((cod_ocorrencia in ('06', '17') and
                 bank_name_brcobranca == 'bradesco') or
                    (cod_ocorrencia in ('06', '10') and
                     bank_name_brcobranca == 'itau') or
                    (cod_ocorrencia in ('01', '06', '07', '09') and
                     bank_name_brcobranca == 'unicred')):

                valor_desconto = valor_juros_mora =\
                    valor_abatimento = valor_tarifa = 0.0

                # Valor Desconto
                if linha_cnab.get('desconto'):
                    valor_desconto = self.cnab_str_to_float(
                        linha_cnab['desconto'])

                    # Valor Liquido precisa ser somado
                    # p/ conciliar com a Fatura
                    valor_recebido += valor_desconto

                    result_row_list.append({
                        'name': 'Desconto (boleto) ' +
                                account_move_line.document_number,
                        'debit': valor_desconto,
                        'credit': 0.0,
                        'account_id': self.journal.default_debit_account_id.id,
                        'type': 'desconto',
                        'ref': account_move_line.document_number,
                    })
                    result_row_list.append({
                        'name': 'Desconto (boleto) ' +
                                account_move_line.document_number,
                        'debit': 0.0,
                        'credit': valor_desconto,
                        'account_id': account_move_line.payment_mode_id.
                        discount_account_id.id,
                        'type': 'desconto',
                        'ref': account_move_line.document_number,
                    })

                # Valor Juros Mora - valor de mora e multa pagos pelo sacado
                if linha_cnab.get('juros_mora'):
                    valor_juros_mora = self.cnab_str_to_float(
                        linha_cnab['juros_mora'])

                    # O valor não está sendo somando pois isso
                    # altera o Valor recebido desbalanceando a
                    # conciliação com a Fatura
                    # valor_recebido += valor_juros_mora

                    result_row_list.append({
                        'name': 'Valor Juros Mora (boleto) ' +
                                account_move_line.document_number,
                        'debit': 0.0,
                        'credit': valor_juros_mora,
                        'account_id': account_move_line.payment_mode_id.
                        interest_fee_account_id.id,
                        'type': 'juros_mora',
                        'ref': account_move_line.document_number,
                        'partner_id': account_move_line.partner_id.id,
                    })

                    result_row_list.append({
                        'name': 'Valor Juros Mora (boleto) ' +
                                account_move_line.document_number,
                        'debit': valor_juros_mora,
                        'credit': 0.0,
                        'account_id': self.journal.default_debit_account_id.id,
                        'type': 'juros_mora',
                        'ref': account_move_line.document_number,
                    })

                # Valor Tarifa
                if linha_cnab.get('valor_tarifa'):
                    valor_tarifa = float(
                        str(linha_cnab['valor_tarifa'][0:4] + '.' +
                            linha_cnab['valor_tarifa'][4:]))

                    # Valor Liquido precisa ser somado
                    # p/ conciliar com a Fatura
                    valor_recebido += valor_tarifa

                    result_row_list.append({
                        'name': 'Tarifas bancárias (boleto) ' +
                                account_move_line.document_number,
                        'debit': 0.0,
                        'credit': valor_tarifa,
                        'account_id': account_move_line.payment_mode_id.
                        tax_account_id.id,
                        'type': 'tarifa',
                        'ref': account_move_line.document_number,
                    })

                    result_row_list.append({
                        'name': 'Tarifas bancárias (boleto) ' +
                                account_move_line.document_number,
                        'debit': valor_tarifa,
                        'credit': 0.0,
                        'type': 'tarifa',
                        'account_id': self.journal.default_debit_account_id.id,
                        'ref': account_move_line.document_number,
                    })

                # Valor Abatimento
                if linha_cnab.get('valor_abatimento'):
                    valor_abatimento = self.cnab_str_to_float(
                        linha_cnab['valor_abatimento'])

                    # Valor Liquido precisa ser somado
                    # p/ conciliar com a Fatura
                    valor_recebido += valor_abatimento

                    result_row_list.append({
                        'name': 'Abatimento (boleto) ' +
                                account_move_line.document_number,
                        'debit': valor_abatimento,
                        'credit': 0.0,
                        'account_id': self.journal.default_debit_account_id.id,
                        'type': 'abatimento',
                        'ref': account_move_line.document_number,
                    })

                    result_row_list.append({
                        'name': 'Abatimento (boleto) ' +
                                account_move_line.document_number,
                        'debit': 0.0,
                        'credit': valor_abatimento,
                        'account_id': account_move_line.payment_mode_id.
                        rebate_account_id.id,
                        'type': 'abatimento',
                        'ref': account_move_line.document_number,
                    })

                vals_evento = {
                    'lot_id': lote_id.id,
                    'occurrence_date': data_ocorrencia,
                    'real_payment_date': data_credito.strftime("%Y-%m-%d"),
                    # 'segmento': evento.servico_segmento,
                    # 'favorecido_nome':
                    #    obj_account_move_line.company_id.partner_id.name,
                    'favored_bank_account_id':
                        account_move_line.payment_mode_id.
                        fixed_journal_id.bank_account_id.id,
                    'own_number': linha_cnab['nosso_numero'],
                    'your_number': account_move_line.document_number,
                    'company_title_identification':
                        linha_cnab['documento_numero'] or
                        account_move_line.document_number,
                    # 'tipo_moeda': evento.credito_moeda_tipo,
                    'title_value': valor_titulo,
                    'payment_value': valor_recebido,
                    'occurrences': descricao_ocorrencia,
                    'bank_payment_line_id':
                        payment_line.bank_line_id.id or False,
                    'invoice_id': account_move_line.invoice_id.id,
                    'due_date': datetime.datetime.strptime(
                        str(linha_cnab['data_vencimento']), "%d%m%y").date(),
                    'discount_value': valor_desconto,
                    'interest_fee_value': valor_juros_mora,
                    'rebate_value': valor_abatimento,
                    'tariff_charge': valor_tarifa,
                }

                if cnab_return_method == 'manual':
                    # Monta o dicionario que sera usado
                    # para criar o Extrato Bancario
                    balance_end_real += valor_recebido
                    line_statement_vals.append({
                        'name': account_move_line.document_number or '?',
                        'amount': valor_recebido,
                        'partner_id': account_move_line.partner_id.id,
                        'ref': account_move_line.ref,
                        'date': account_move_line.date,
                        'amount_currency': valor_recebido,
                        'currency_id': account_move_line.currency_id.id,
                    })

                # Linha da Fatura a ser reconciliada
                if cnab_return_method == 'automatic':
                    result_row_list.append({
                         'name': account_move_line.invoice_id.number,
                         'debit': 0.0,
                         'credit': valor_recebido,
                         'move_line': account_move_line,
                         'invoice_id': account_move_line.invoice_id.id,
                         'type': 'liquidado',
                         'bank_payment_line_id':
                         payment_line.bank_line_id.id or False,
                         'ref': account_move_line.own_number,
                         'account_id': account_move_line.account_id.id,
                         'partner_id': account_move_line.partner_id.id,
                    })

            else:
                vals_evento = {
                    'lot_id': lote_id.id,
                    'occurrences': descricao_ocorrencia,
                    'occurrence_date': data_ocorrencia,
                    'own_number': account_move_line.own_number,
                    'your_number': account_move_line.document_number,
                    'title_value': valor_titulo,
                }

            self.env['l10n_br.cnab.evento'].create(vals_evento)

            lote_id.total_valores = total_valores
            lote_id.qtd_registros = quantidade_registros
            self.num_lotes = 1
            self.num_eventos = quantidade_registros

        # Forma Manual do Retorno CNAB
        # Criacao de um Extrato Bancario, isso permite o tratamento de alguma
        # diferença que tenha restado já que os valores de Juros/Mora, Tarifas,
        # Desconto e Abatimento estão sendo lançados em uma entrada de Diário
        # separada e portanto na maioria dos casos o valor no extrato vai estar
        # de acordo com o valor da fatura
        if line_statement_vals:
            vals_bank_statement = {
                'name': self.journal.sequence_id.next_by_id(),
                'journal_id': self.journal.id,
                'balance_end_real': balance_end_real,
            }
            statement = self.env[
                'account.bank.statement'].create(vals_bank_statement)
            statement_line_obj = self.env['account.bank.statement.line']
            for line in line_statement_vals:
                line['statement_id'] = statement.id
                statement_line_obj.create(line)

        return result_row_list

    def cnab_str_to_float(self, value):
        if len(value) == 13:
            value_float = float(
                str(value[0:11] + '.' + value[11:]))
            return value_float

    def get_move_vals(self):
        """This method return a dict of vals that ca be passed to create method
        of statement.
        :return: dict of vals that represent additional infos for the statement
        """
        return {
            'name': 'Retorno CNAB - ' + str(
                fields.Datetime.now().date().strftime('%d/%m/%Y')),
            'date': fields.Datetime.now(),
            'ref': self.move_ref or '/'
        }

    def get_move_line_vals(self, line, *args, **kwargs):
        """This method must return a dict of vals that can be passed to create
        method of statement line in order to record it. It is the
        responsibility of every parser to give this dict of vals, so each one
        can implement his own way of recording the lines.
            :param:  line: a dict of vals that represent a line of
              result_row_list
            :return: dict of values to give to the create method of statement
              line, it MUST contain at least:
                {
                    'name':value,
                    'date':value,
                    'amount':value,
                    'ref':value,
                    'label':value,
                    'commission_amount':value,
                }
        """

        vals = {
            'name': line['name'] or line.get('source'),
            'credit': line['credit'],
            'debit': line['debit'],
            'already_completed': False,
            'partner_id': None,
            'ref': line['ref'],
            'account_id': line['account_id'],
        }
        if line['type'] == 'liquidado':
            vals.update({
                'invoice_id': line['invoice_id'],
                'partner_id': line['partner_id'],
                'already_completed': True,
                }
            )
        elif line["type"] == "juros_mora" and line['credit'] > 0.0:
            vals.update({
                'partner_id': line['partner_id']})

        return vals
