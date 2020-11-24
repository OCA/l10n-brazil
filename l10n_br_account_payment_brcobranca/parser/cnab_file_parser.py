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
        self.cnab_return_events = []

    @classmethod
    def parser_for(cls, parser_name):
        if parser_name == 'cnab400':
            return parser_name == 'cnab400'
        elif parser_name == 'cnab240':
            return parser_name == 'cnab240'

    def parse(self, filebuffer):

        files = {'data': base64.b64decode(filebuffer)}

        api_address = self.env[
            'ir.config_parameter'].sudo().get_param(
            'l10n_br_account_payment_brcobranca.boleto_cnab_api')
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

        self.result_row_list = self.process_return_file(data)

        yield self.result_row_list

    @api.multi
    def process_return_file(self, data):

        #          Forma de Lançamento do Retorno
        # Criação de uma Entrada de Diário com os valores de desconto,
        # juros/mora, tarifa bancaria, abatimento, valor total
        #
        # Quando marcada a opção de Reconciliação Automatica no Diário
        # a Fatura será Reconciliada e a Entrada de Diário será movida
        # para o status Lançado

        #          Valor Recebido diferente do Valor no Odoo
        # Para que a Fatura/Nota Fiscal no Odoo seja completamente reconciliada
        # e o seu status seja alterado de Aberto para Pago é preciso que
        # a soma dos lançamentos(account.move.line) criados sejam iguais ao
        # valor da account_move_line em aberto.
        #
        #                      Valor Menor
        # Os valores de Desconto e Abatimento estão sendo adicionados na
        # reconciliação para que o valor total fique igual, exemplo:
        #        Odoo               Valores arquivo CNAB
        #    Valor Odoo   | Valor Recebido | Valor Abatimento |Valor Desconto
        #       100       |     80         |       10         |     10
        # Caso o valor ainda seja menor nada pode ser feito aqui, pois
        # significa que o cliente pagou um valor menor sem relação com o
        # Abatimento e ou Desconto e que ainda está em Aberto junto ao banco.
        # TODO: Existe a possibilidade de Pagar um valor menor junto ao banco ?
        # Se for preciso Baixar esse valor o processo deverá ser utilizar o
        # wizard de atualizações do CNAB, na account.move.line referente,
        # pedindo a Baixa do Título o que irá gerar um nova Linha/Instrução
        # CNAB a ser enviada ao Banco.
        #
        #                   Valor Maior
        # Caso comum onde o devido o valor de Juros Mora/Multa faz com que
        # os valores fiquem diferentes, exemplo:
        #        Odoo               Valores arquivo CNAB
        #    Valor Odoo   | Valor Recebido | Juros Mora + Multa*
        #       100       |     110        |       10
        #
        # *valores vem somados no CNAB Unicred 400, seria um padrão ?
        #
        # Não é possível relacionar esse lançamento contabil diretamente isso
        # causa erro, seria preciso "Cancelar o Lançamento" da account.move(
        # referente a invoice que gerou o CNAB) é criar uma nova linha
        # assim aumentando o valor original da Fatura, na primeira linha que
        # fosse recebida esse processo até poderia funcionar mas no caso de uma
        # segunda, terceira, etc acredito que o programa já não permitiria mais
        # Cancelar o Lançamento existindo reconciliações parciais.
        # Por isso Nesse caso é preciso alterar o Valor Recebido
        # ( Valor Recebido - Valor Juros Mora/Multa )
        # TODO: Deveria existir uma forma de mostrar o Valor de Juros/Multa na
        #  tela da Fatura/Invoice, e assim o usuário poder visualizar isso ?
        # Porque não vai existir um relacionamento direto de conciliação, apenas a
        # referencia no campo name e invoice_id da account.move.line

        # Lista com os dados q poderão ser usados
        # na criação das account move line
        result_row_list = []

        for linha_cnab in data:

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

            valor_titulo = self.cnab_str_to_float(
                linha_cnab['valor_titulo'])

            data_ocorrencia = datetime.date.today()
            cod_ocorrencia = str(linha_cnab['codigo_ocorrencia'])
            # Cada Banco pode possuir um Codigo de Ocorrencia distinto,
            # mesmo no caso do 240, ver Unicred na pasta de dados do
            # l10n_br_account_payment_order
            payment_method_cnab = self.env['account.payment.method'].search([
                ('payment_type', '=', 'inbound'),
                ('code', '=', self.parser_name[4:7])
            ])
            cnab_return_move_code = self.env[
                'l10n_br_cnab.return.move.code'].search([
                    ('bank_ids', 'in', self.bank.id),
                    ('payment_method_ids', 'in', payment_method_cnab.id),
                    ('code', '=', cod_ocorrencia)
                ])
            if cnab_return_move_code:
                descricao_ocorrencia = \
                    cod_ocorrencia + '-' + cnab_return_move_code.name
            else:
                descricao_ocorrencia = \
                    cod_ocorrencia + '-' + 'CÓDIGO DA DESCRIÇÃO NÃO ENCONTRADO'

            # Campo especifico do Bradesco
            if bank_name_brcobranca == 'bradesco':
                if (linha_cnab['data_ocorrencia'] == '000000' or
                        not linha_cnab['data_ocorrencia']):
                    data_ocorrencia = linha_cnab['data_de_ocorrencia']
                else:
                    data_ocorrencia = datetime.datetime.strptime(
                        str(linha_cnab['data_ocorrencia']), "%d%m%y").date()

            # Nosso numero vem com o Digito Verificador
            # ex.: 00000000000002010
            nosso_numero_sem_dig = linha_cnab['nosso_numero'][:-1]

            # nosso_numero_sem_dig.strip("0")
            # ex.: 201
            nosso_numero_sem_zeros = nosso_numero_sem_dig.strip('0')

            # No arquivo de retorno do CNAB o campo pode ter um tamanho
            # diferente, o tamanho do campo é preenchido na totalidade
            # com zeros a esquerda, e no odoo o tamanho do sequencial pode
            # estar diferente
            # ex.: retorno cnab 0000000000000201 own_number 0000000201
            # o campo own_number_without_zfill foi a forma que encontrei
            # para poder usar o nosso_numero_cnab_retorno.strip("0") e
            # ter algo:
            #  ex.: retorno cnab 201 own_number_without_zfill 201
            # Assim o search consegue encontrar a move line
            # relacionada ao Evento.
            # Podem existir sequencias do nosso numero/own_number iguais entre
            # bancos diferentes, porém os Diario/account.journal
            # não pode ser o mesmo.
            account_move_line = self.env['account.move.line'].search([
                ('own_number_without_zfill', '=', nosso_numero_sem_zeros),
                ('journal_payment_mode_id', '=', self.journal.id)
            ])

            # Linha não encontrada
            if not account_move_line:
                self.cnab_return_events.append({
                    'occurrences': descricao_ocorrencia,
                    'occurrence_date': data_ocorrencia,
                    'str_motiv_a':
                        ' * - BOLETO NÃO ENCONTRADO.',
                    'own_number': linha_cnab['nosso_numero'],
                    'your_number': linha_cnab['documento_numero'],
                    'title_value': valor_titulo,
                })
                continue

            payment_line = self.env['account.payment.line'].search(
                [('move_line_id', '=', account_move_line.id)]
            )

            # Codigos de Movimento de Retorno - Liquidação
            cnab_liq_move_code = []
            for move_code in account_move_line.payment_mode_id.\
                    cnab_liq_return_move_code_ids:
                cnab_liq_move_code.append(move_code.code)

            if cod_ocorrencia in cnab_liq_move_code:

                valor_recebido = valor_desconto = valor_juros_mora =\
                    valor_abatimento = valor_tarifa = 0.0

                if linha_cnab['valor_recebido']:
                    valor_recebido = self.cnab_str_to_float(
                        linha_cnab['valor_recebido'])

                if (linha_cnab['data_credito'] == '000000' or
                        not linha_cnab['data_credito']):
                    data_credito = linha_cnab['data_credito']
                else:
                    data_credito = datetime.datetime.strptime(
                        str(linha_cnab['data_credito']), "%d%m%y").date()

                # Valor Desconto
                if linha_cnab.get('desconto'):
                    valor_desconto = self.cnab_str_to_float(
                        linha_cnab['desconto'])
                    if valor_desconto > 0.0:
                        result_row_list.append({
                            'name': 'Desconto (boleto) ' +
                                    account_move_line.document_number,
                            'debit': valor_desconto,
                            'credit': 0.0,
                            'account_id': account_move_line.payment_mode_id.
                            discount_account_id.id,
                            'type': 'desconto',
                            'ref': account_move_line.document_number,
                            'invoice_id': account_move_line.invoice_id.id,
                        })

                        # Usado para Conciliar a Fatura
                        # Write Off necessário para ser possível a conciliação
                        result_row_list.append({
                            'name': 'Desconto (boleto) ' +
                                    account_move_line.document_number,
                            'debit': 0.0,
                            'credit': valor_desconto,
                            'type': 'desconto',
                            'account_id': account_move_line.account_id.id,
                            'ref': account_move_line.own_number,
                            'invoice_id': account_move_line.invoice_id.id,
                            'partner_id': account_move_line.partner_id.id,
                        })

                # Valor Juros Mora - valor de mora e multa pagos pelo sacado
                if linha_cnab.get('juros_mora'):
                    valor_juros_mora = self.cnab_str_to_float(
                        linha_cnab['juros_mora'])

                    if valor_juros_mora > 0.0:

                        # Usado para Conciliar a Fatura.
                        # Necessário atualizar o Valor Recebido pois o Odoo
                        # não aceita a conciliação com um valor maior do que
                        # o informado.
                        valor_recebido -= valor_juros_mora

                        result_row_list.append({
                            'name': 'Valor Juros Mora (boleto) ' +
                                    account_move_line.document_number,
                            'debit': 0.0,
                            'credit': valor_juros_mora,
                            'type': 'juros_mora',
                            'account_id': account_move_line.account_id.id,
                            'ref': account_move_line.document_number,
                            'invoice_id': account_move_line.invoice_id.id,
                            'partner_id': account_move_line.partner_id.id,
                        })

                        result_row_list.append({
                            'name': 'Valor Juros Mora (boleto) ' +
                                    account_move_line.document_number,
                            'debit': valor_juros_mora,
                            'credit': 0.0,
                            'account_id': account_move_line.payment_mode_id.
                            interest_fee_account_id.id,
                            'journal_id': account_move_line.journal_id.id,
                            'type': 'juros_mora',
                            'ref': account_move_line.document_number,
                            'invoice_id': account_move_line.invoice_id.id,
                            'partner_id': account_move_line.partner_id.id,
                        })

                # Valor Tarifa
                if linha_cnab.get('valor_tarifa'):
                    valor_tarifa = self.cnab_str_to_float(
                        linha_cnab['valor_tarifa'])

                    if valor_tarifa > 0.0:
                        # Usado para Conciliar a Fatura
                        result_row_list.append({
                            'name': 'Tarifas bancárias (boleto) ' +
                                    account_move_line.document_number,
                            'debit': 0.0,
                            'credit': valor_tarifa,
                            'account_id': account_move_line.account_id.id,
                            'type': 'tarifa',
                            'ref': account_move_line.own_number,
                            'invoice_id': account_move_line.invoice_id.id,
                            'partner_id': account_move_line.partner_id.id,
                        })

                        result_row_list.append({
                            'name': 'Tarifas bancárias (boleto) ' +
                                    account_move_line.document_number,
                            'debit': valor_tarifa,
                            'credit': 0.0,
                            'type': 'tarifa',
                            'account_id': account_move_line.payment_mode_id.
                            tariff_charge_account_id.id,
                            'ref': account_move_line.document_number,
                            'invoice_id': account_move_line.invoice_id.id,
                        })

                # Valor Abatimento
                if linha_cnab.get('valor_abatimento'):
                    valor_abatimento = self.cnab_str_to_float(
                        linha_cnab['valor_abatimento'])

                    if valor_abatimento:
                        result_row_list.append({
                            'name': 'Abatimento (boleto) ' +
                                    account_move_line.document_number,
                            'debit': valor_abatimento,
                            'credit': 0.0,
                            'account_id': account_move_line.payment_mode_id.
                            rebate_account_id.id,
                            'type': 'abatimento',
                            'ref': account_move_line.document_number,
                            'invoice_id': account_move_line.invoice_id.id,
                        })

                        # Usado para Conciliar a Fatura
                        # Write Off necessário para ser possível a conciliação
                        result_row_list.append({
                            'name': 'Abatimento (boleto) ' +
                                    account_move_line.document_number,
                            'debit': 0.0,
                            'credit': valor_abatimento,
                            'type': 'abatimento',
                            'account_id': account_move_line.account_id.id,
                            'ref': account_move_line.own_number,
                            'invoice_id': account_move_line.invoice_id.id,
                            'partner_id': account_move_line.partner_id.id,
                        })

                # Linha da Fatura a ser reconciliada
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

                # CNAB LOG
                self.cnab_return_events.append({
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
                })

            else:
                # Nos codigos de retorno cadastrados no Data do modulo
                # l10n_br_account_payment_order o 02 se refere a
                # Entrada Confirmada e 03 Entrada Rejeitada.
                # TODO: Estou considerando que seja um padrão, existem
                #  exceções ?
                #  Caso exista será preciso criar o campo no payment.mode
                #  para informa-lo como nos outros casos.
                if cod_ocorrencia == '02':
                    account_move_line.cnab_state = 'accepted'
                elif cod_ocorrencia == '03':
                    # TODO - algo a mais a ser feito ?
                    account_move_line.cnab_state = 'not_accepted'

                self.cnab_return_events.append({
                    'occurrences': descricao_ocorrencia,
                    'occurrence_date': data_ocorrencia,
                    'own_number': account_move_line.own_number,
                    'your_number': account_move_line.document_number,
                    'title_value': valor_titulo,
                })

        return result_row_list

    def cnab_str_to_float(self, value):
        # Até onde vi independente do tamanho do campo os
        # 2 ultimos caracteres se referem ao decimal
        decimal_point = len(value) - 2
        value_float = float(
            str(value[0:decimal_point] +
                '.' + value[decimal_point:]))
        return value_float

    def get_move_vals(self):
        """This method return a dict of vals that ca be passed to create method
        of statement.
        :return: dict of vals that represent additional infos for the statement
        """
        return {
            'name': 'Retorno CNAB - Banco ' + self.bank.short_name + ' - Conta '
                    + self.journal.bank_account_id.acc_number,
            'date': fields.Datetime.now(),
            # TODO  - Campo está sendo preenchido em outro lugar
            'ref': 'Retorno CNAB',
            'is_cnab': True,
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
            'partner_id': None,
            'ref': line['ref'],
            'account_id': line['account_id'],
            'invoice_id': line['invoice_id'],
            'already_completed': True,
        }
        if line['type'] in (
                'liquidado', 'tarifa', 'juros_mora',
                'desconto', 'abatimento') and line['credit'] > 0.0:
            vals.update({
                'partner_id': line['partner_id'],
                }
            )

        return vals
