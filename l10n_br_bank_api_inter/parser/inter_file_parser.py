# @ 2021 KMEE - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
import logging

logger = logging.getLogger(__name__)


class InterFileParser:
    """
    # TODO
    """

    def __init__(self, journal, *args, **kwargs):
        # The name of the parser as it will be called
        # self.parser_name = journal.import_type
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

    def parse(self, filebuffer):
        self.result_row_list = self.process_return_file(self.data)
        yield self.result_row_list

    def _code_log(self):
        pass

    def process_return_file(self, data):

        #          Forma de Lançamento do Retorno
        # Em caso de Pagamento/Liquidação é feita a criação de uma Entrada de
        # Diário para cada linha do arquivo CNAB com os valores de desconto,
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
        # Os valores de Desconto e Abatimento estão sendo adicionados no
        # lançamento referente ao pagamento para que o valor total fique
        # igual, exemplo:
        #        Odoo               Valores arquivo CNAB
        #    Valor Odoo   | Valor Recebido | Valor Abatimento |Valor Desconto
        #       100       |     80         |       10         |     10
        #
        # O Valor Recebido a ser lançado será 100.
        #
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
        # O Valor Recebido a ser lançado será 100.
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
        # Porque não vai existir um relacionamento direto de conciliação,
        # apenas a referencia no campo name e invoice_id da account.move.line,
        # e caso se queira saber os detalhes será preciso olhar a Entrada de
        # Diário referente.

        if self._code_log() == data["situacao"]:
            return

        valor_titulo = data["valorNominal"]

        data_ocorrencia = datetime.date.today()
        cod_ocorrencia = data["situacao"]

        # TODO: A mensagem de retorno é apenas o código da situação, seria interessante
        #   retornar uma mensagem menos técnica e mais 'acessível' ao usuário.
        descricao_ocorrencia = data["situacao"]

        # TODO Revisar o preenchimento desses campos no momento da emissão
        nosso_numero_sem_dig = data["nossoNumero"][:-1]
        nosso_numero_sem_zeros = nosso_numero_sem_dig.lstrip("0")
        account_move_line = self.env["account.move.line"].search(
            [
                ("own_number_without_zfill", "=", nosso_numero_sem_zeros),
                ("journal_payment_mode_id", "=", self.journal.id),
            ]
        )

        # Linha não encontrada
        if not account_move_line:
            self.cnab_return_events.append(
                {
                    "occurrences": descricao_ocorrencia,
                    "occurrence_date": data_ocorrencia,
                    "str_motiv_a": " * - BOLETO NÃO ENCONTRADO.",
                    "own_number": data["nossoNumero"],
                    "your_number": data["seuNumero"],
                    "title_value": valor_titulo,
                }
            )

        payment_line = self.env["account.payment.line"].search(
            [("move_line_id", "=", account_move_line.id)]
        )

        # A Linha de Pagamento pode ter N bank.payment.line
        # estamos referenciando apenas a referente a que iniciou
        # o CNAB
        # TODO: Deveria relacionar todas ?
        # bank_line = payment_line.bank_line_id.filtered(
        #     lambda b: b.mov_instruction_code_id.id
        #               == payment_line.payment_mode_id.cnab_sending_code_id.id
        # )
        bank_line = payment_line.bank_line_id

        # Codigos de Movimento de Retorno - Liquidação
        cnab_liq_move_code = []
        for (
            move_code
        ) in account_move_line.payment_mode_id.cnab_liq_return_move_code_ids:
            cnab_liq_move_code.append(move_code.code)

        favored_bank_account = (
            account_move_line.payment_mode_id.fixed_journal_id.bank_account_id
        )
        cnab_return_log_event = {
            "occurrences": descricao_ocorrencia,
            "occurrence_date": data_ocorrencia,
            "own_number": account_move_line.own_number,
            "your_number": account_move_line.document_number,
            "title_value": valor_titulo,
            "bank_payment_line_id": bank_line.id or False,
            "invoice_id": account_move_line.invoice_id.id,
            "due_date": datetime.datetime.strptime(
                str(data["dataVencimento"]), "%d%m%y"
            ).date(),
            "move_line_id": account_move_line.id,
            "company_title_identification": data["seuNumero"]
            or account_move_line.document_number,
            "favored_bank_account_id": favored_bank_account.id,
            # TODO: Campo Segmento é referente ao CNAB 240, o
            #  BRCobranca parece não informar esse campo no retorno,
            #  é preciso validar isso nesse caso.
            # 'segmento': evento.servico_segmento,
            # 'favorecido_nome':
            #    obj_account_move_line.company_id.partner_id.name,
            # 'tipo_moeda': evento.credito_moeda_tipo,
        }

        # Caso de Pagamento deve criar os Lançamentos de Diário
        if cod_ocorrencia == "PAGO":

            row_list, log_event_payment = self._get_accounting_entries(
                data, account_move_line, bank_line
            )
            self.result_row_list.append(row_list)
            cnab_return_log_event.update(log_event_payment)
        else:
            # No caso do Banco Inter, a única forma de saber se um boleto foi
            # aceito ou não é através de sua situação, ou seja, sua situação
            # sempre será definida como "EMABERTO" assim que o boleto for gerado.
            if cod_ocorrencia == "EMABERTO":
                account_move_line.cnab_state = "accepted"

        # Inclui o LOG do Evento CNAB
        self.cnab_return_events.append(cnab_return_log_event)

        return self.result_row_list

    def _get_description_occurrence(self, payment_method_cnab, cod_ocorrencia):
        cnab_return_move_code = self.env["l10n_br_cnab.return.move.code"].search(
            [
                ("bank_ids", "in", self.bank.id),
                ("payment_method_ids", "in", payment_method_cnab.id),
                ("code", "=", cod_ocorrencia),
            ]
        )
        if cnab_return_move_code:
            descricao_ocorrencia = cod_ocorrencia + "-" + cnab_return_move_code.name
        else:
            descricao_ocorrencia = (
                cod_ocorrencia + "-" + "CÓDIGO DA DESCRIÇÃO NÃO ENCONTRADO"
            )

        return descricao_ocorrencia

    def _get_accounting_entries(self, data, account_move_line, bank_line):
        row_list = []
        valor_nominal = (
            valor_desconto
        ) = valor_juros_mora = valor_abatimento = valor_multa = valor_recebido = 0.0

        if data["valorNominal"]:
            # Campor Valor Nominal vem com o valor do boleto
            valor_nominal = data["valorNominal"]

        if data["valorTotalRecebimento"]:
            valor_recebido = data["valorTotalRecebimento"]

        data_credito = data["dataHoraSituacao"]

        # TODO: O desconto ainda não está sendo considerado durante o processo de
        #  emissão e além disso é necessário ver se o Odoo vai contemplar todas as
        #  formas de desconto possíveis no Banco Inter.
        # As formas de desconto disponibilizadas pelo Banco Inter são:
        #   NAOTEMDESCONTO, VALORFIXODATAINFORMADA, PERCENTUALDATAINFORMADA,
        #   VALORANTECIPACAODIACORRIDO, VALORANTECIPACAODIAUTIL,
        #   PERCENTUALVALORNOMINALDIACORRIDO, PERCENTUALVALORNOMINALDIAUTIL
        # TODO: Por enquanto está sendo considerado apenas um tipo de desconto, que está
        #   de acordo com a data de vencimento informada no boleto. Porém, ainda é
        #   necessário que seja implementado os outros métodos suportados pelo Banco
        #   Inter principalmente na visão do Odoo, já que ele considera apenas uma
        #   forma de desconto e o Banco Inter aceita até três, cada uma com uma data
        #   diferente de validade.
        # Valor Desconto
        if (
            datetime.strptime(data["dataVencimento"], "%d/%m/%Y")
            <= datetime.date.today()
        ):
            taxa_desconto1 = data["desconto1"]["taxa"]
            valor_desconto = taxa_desconto1 * valor_nominal
            if valor_desconto > 0.0:
                row_list.append(
                    {
                        "name": "Desconto (boleto) "
                        + account_move_line.document_number,
                        "debit": valor_desconto,
                        "credit": 0.0,
                        "account_id": (
                            account_move_line.payment_mode_id.discount_account_id.id
                        ),
                        "type": "desconto",
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                    }
                )

                row_list.append(
                    {
                        "name": "Desconto (boleto) "
                        + account_move_line.document_number,
                        "debit": 0.0,
                        "credit": valor_desconto,
                        "type": "desconto",
                        "account_id": self.journal.default_credit_account_id.id,
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                        "partner_id": account_move_line.partner_id.id,
                    }
                )

        # Valor Juros Mora - valor de mora e multa pagos pelo sacado
        # As formas de Juros Moras disponibilizadas pelo Banco Inter são:
        #   VALORDIA, TAXAMENSAL e ISENTO.
        if (
            datetime.strptime(data["dataVencimento"], "%d/%m/%Y")
            <= datetime.date.today()
        ):
            taxa_juros_mora = data["mora"]["taxa"]
            valor_juros_mora = taxa_juros_mora * valor_nominal

            if valor_juros_mora > 0.0:
                row_list.append(
                    {
                        "name": "Valor Juros Mora (boleto) "
                        + account_move_line.document_number,
                        "debit": 0.0,
                        "credit": valor_juros_mora,
                        "type": "juros_mora",
                        "account_id": (
                            account_move_line.payment_mode_id.interest_fee_account_id.id
                        ),
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                        "partner_id": account_move_line.partner_id.id,
                    }
                )

                row_list.append(
                    {
                        "name": "Valor Juros Mora (boleto) "
                        + account_move_line.document_number,
                        "debit": valor_juros_mora,
                        "credit": 0.0,
                        "account_id": self.journal.default_credit_account_id.id,
                        "journal_id": account_move_line.journal_id.id,
                        "type": "juros_mora",
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                        "partner_id": account_move_line.partner_id.id,
                    }
                )

        # TODO: Não há uma tarifa que é cobrada pelo Banco Inter para emissão de boletos
        #   por isso o campo "Tarifa" foi alterado para multa.
        # O Banco Inter disponibiliza as seguintes opções para suas multas:
        #   NAOTEMMULTA, VALORFIXO e PERCENTUAL
        if (
            datetime.strptime(data["dataVencimento"], "%d/%m/%Y")
            <= datetime.date.today()
        ):
            taxa_multa = data["multa"]["taxa"]
            valor_multa = valor_nominal * taxa_multa

            if valor_multa > 0.0:
                # Usado para Conciliar a Fatura
                row_list.append(
                    {
                        "name": "Valor multa (boleto) "
                        + account_move_line.document_number,
                        "debit": 0.0,
                        "credit": valor_multa,
                        "account_id": self.journal.default_credit_account_id.id,
                        "type": "tarifa",
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                        "partner_id": account_move_line.company_id.partner_id.id,
                    }
                )

                # Avoid error in pre commit
                tariff_charge_account = (
                    account_move_line.payment_mode_id.tariff_charge_account_id
                )
                row_list.append(
                    {
                        "name": "Tarifas bancárias (boleto) "
                        + account_move_line.document_number,
                        "debit": self.valor_tarifa,
                        "credit": 0.0,
                        "type": "tarifa",
                        "account_id": tariff_charge_account.id,
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                    }
                )

        # Valor Abatimento
        if data.get("valorAbatimento"):
            valor_abatimento = data["valorAbatimento"]

            if valor_abatimento:
                row_list.append(
                    {
                        "name": "Abatimento (boleto) "
                        + account_move_line.document_number,
                        "debit": valor_abatimento,
                        "credit": 0.0,
                        "account_id": (
                            account_move_line.payment_mode_id.rebate_account_id.id
                        ),
                        "type": "abatimento",
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                    }
                )

                row_list.append(
                    {
                        "name": "Abatimento (boleto) "
                        + account_move_line.document_number,
                        "debit": 0.0,
                        "credit": valor_abatimento,
                        "type": "abatimento",
                        "account_id": self.journal.default_credit_account_id.id,
                        "ref": account_move_line.document_number,
                        "invoice_id": account_move_line.invoice_id.id,
                        "partner_id": account_move_line.partner_id.id,
                    }
                )

        # Linha da Fatura a ser reconciliada com o Pagamento em Aberto,
        # necessário atualizar o Valor Recebido pois o Odoo não
        # aceita a conciliação nem com um Valor Menor ou Maior.
        valor_recebido_calculado = (
            valor_nominal + valor_desconto + valor_abatimento + valor_multa
        ) - valor_juros_mora

        row_list.append(
            {
                "name": account_move_line.invoice_id.number,
                "debit": 0.0,
                "credit": valor_recebido_calculado,
                "move_line": account_move_line,
                "invoice_id": account_move_line.invoice_id.id,
                "type": "liquidado",
                "bank_payment_line_id": bank_line.id or False,
                "ref": account_move_line.own_number,
                "account_id": account_move_line.account_id.id,
                "partner_id": account_move_line.partner_id.id,
                "date": data_credito,
            }
        )

        # CNAB LOG
        log_event_payment = {
            "real_payment_date": data_credito.strftime("%Y-%m-%d"),
            "payment_value": valor_recebido,
            "discount_value": valor_desconto,
            "interest_fee_value": valor_juros_mora,
            "rebate_value": valor_abatimento,
            "tariff_charge": valor_multa,
        }

        return row_list, log_event_payment

    def get_move_vals(self):
        """This method return a dict of vals that ca be passed to create method
        of statement.
        :return: dict of vals that represent additional infos for the statement
        """
        return {
            "name": "Retorno CNAB - Banco "
            + self.bank.short_name
            + " - Conta "
            + self.journal.bank_account_id.acc_number,
            "is_cnab": True,
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
            "name": line["name"] or line.get("source"),
            "credit": line["credit"],
            "debit": line["debit"],
            "partner_id": None,
            "ref": line["ref"],
            "account_id": line["account_id"],
            "invoice_id": line["invoice_id"],
            "already_completed": True,
        }
        if (
            line["type"]
            # TODO: Está considerando apenas o valor do desconto1, mas implementar
            #   depois para os descontos: desconto2 e desconto3.
            in (
                "valorTotalRecebimento",
                "multa",
                "mora",
                "desconto1",
                "valorAbatimento",
            )
            and line["credit"] > 0.0
        ):
            vals.update(
                {
                    "partner_id": line["partner_id"],
                }
            )

        return vals
