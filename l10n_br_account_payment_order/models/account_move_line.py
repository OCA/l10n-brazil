# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants import (
    BR_CODES_PAYMENT_ORDER,
    ESTADOS_CNAB,
    PAGAMENTO_FORNECEDOR,
    SITUACAO_PAGAMENTO,
)


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = [_name, "l10n_br_cnab.change.methods"]

    # As linhas de cobrança precisam ser criadas conforme sequencia de
    # Data de Vencimentos/date_maturity senão ficam fora de ordem:
    #  ex.: own_number 201 31/12/2020, own_number 202 18/11/2020
    #  Isso causa confusão pois a primeira parcela fica como sendo a segunda.
    @property
    def _order(self):
        if self.env.company.country_id.code == "BR":
            return "date desc, date_maturity asc, move_name desc, id"
        return super()._order

    cnab_state = fields.Selection(
        selection=ESTADOS_CNAB,
        string="Estados CNAB",
        copy=False,
    )

    own_number = fields.Char(
        string="Nosso Numero",
        copy=False,
    )

    # No arquivo de retorno do CNAB o campo pode ter um tamanho diferente,
    # o tamanho do campo é preenchido na totalidade com zeros a esquerda,
    # e no odoo o tamanho do sequencial pode estar diferente
    # ex.: retorno cnab 0000000000000201 own_number 0000000201
    # o campo abaixo foi a forma que encontrei para poder usar o
    # nosso_numero_cnab_retorno.strip("0") e ter algo:
    #  ex.: retorno cnab 201 own_number_without_zfill 201
    # Assim o metodo que faz o retorno do CNAB consegue encontrar
    # a move line relacionada ao Evento.
    own_number_without_zfill = fields.Char(
        compute="_compute_own_number_without_zfill",
        store=True,
        copy=False,
    )

    # Podem existir sequencias do nosso numero/own_number iguais entre bancos
    # diferentes, porém o Diario/account.journal não pode ser o mesmo.
    journal_payment_mode_id = fields.Many2one(
        comodel_name="account.journal",
        compute="_compute_journal_payment_mode",
        store=True,
        copy=False,
    )

    document_number = fields.Char(
        string="Número documento",
        copy=False,
    )

    company_title_identification = fields.Char(
        string="Identificação Titulo Empresa",
        copy=False,
    )

    payment_situation = fields.Selection(
        selection=SITUACAO_PAGAMENTO,
        string="Situação do Pagamento",
        default="inicial",
        copy=False,
    )

    cnab_config_id = fields.Many2one(
        related="payment_mode_id.cnab_config_id",
    )

    boleto_discount_perc = fields.Float(
        string="Desconto de pontualidade",
        digits="Account",
        help="Percentual de Desconto até a Data de Vencimento",
        related="cnab_config_id.boleto_discount_perc",
    )

    instructions = fields.Text(
        string="Instruções de cobrança",
        readonly=True,
        copy=False,
    )

    # TODO: Confirmar o caso de uso de diferentes modos de pagto na mesma
    #  account.invoice
    payment_mode_id = fields.Many2one(string="Modo de Pagamento")

    last_change_reason = fields.Text(
        readonly=True,
        string="Justificativa",
        copy=False,
    )

    instruction_move_code_id = fields.Many2one(
        comodel_name="l10n_br_cnab.code",
        string="Código da Instrução para Movimento",
        help="Campo G061 do CNAB",
        copy=False,
    )

    # Usados para deixar invisiveis/somente leitura
    # os campos relacionados ao CNAB
    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        related="payment_mode_id.payment_method_id",
        string="Payment Method",
    )

    payment_method_code = fields.Char(
        related="payment_method_id.code",
        store=True,
        string="Payment Method Code",
    )

    cnab_return_line_ids = fields.One2many(
        string="Retornos CNAB",
        comodel_name="l10n_br_cnab.return.event",
        readonly=True,
        inverse_name="move_line_id",
    )

    def _get_default_service_type(self):
        if self.move_id.move_type == "in_invoice":
            return PAGAMENTO_FORNECEDOR

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        # PIX pode ser necessário tanto para integragração via CNAB quanto API.
        if self.partner_id.pix_key_ids:
            vals["partner_pix_id"] = self.partner_id.pix_key_ids[0].id
        # Preenchendo apenas nos casos CNAB
        if self.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER:
            vals.update(
                {
                    "own_number": self.own_number,
                    "document_number": self.document_number,
                    "company_title_identification": self.company_title_identification,
                    # Codigo de Instrução do Movimento
                    "instruction_move_code_id": self.instruction_move_code_id.id,
                    "communication_type": "cnab",
                    # Campos abaixo estão sendo adicionados devido ao problema de
                    # Ordens de Pagto vinculadas devido o ondelete=restrict no
                    # campo move_line_id do account.payment.line
                    # TODO: Aguardando a possibilidade de alteração no
                    #  modulo account_payment_order na v14
                    "ml_maturity_date": self.date_maturity,
                    "move_id": self.move_id.id,
                    "service_type": self._get_default_service_type(),
                    "discount_value": self.currency_id.round(
                        self.amount_currency * (self.boleto_discount_perc / 100)
                    ),
                }
            )

            # Se for uma solicitação de baixa do título é preciso informar o
            # campo debit o codigo original coloca o amount_residual
            if (
                self.cnab_config_id.write_off_code_id
                and self.instruction_move_code_id
                == self.cnab_config_id.write_off_code_id
            ):
                vals["amount_currency"] = self.credit or self.debit

            if self.env.context.get("rebate_value"):
                vals["rebate_value"] = self.env.context.get("rebate_value")

            if self.env.context.get("discount_value"):
                vals["discount_value"] = self.env.context.get("discount_value")

        # Dados do Split Payment do IBS/CBS, veja
        # https://github.com/OCA/l10n-brazil/issues/5146
        vals.update(self._prepare_split_payment_line_vals())

        return vals

    def _prepare_split_payment_line_vals(self):
        """
        Prepara os valores de IBS/CBS e a Chave do Documento Fiscal (DF-e)
        usados no Split Payment (LC 214/2025) a partir do Documento Fiscal da
        Fatura. Os campos só são preenchidos quando existe a relação do
        account.move com o l10n_br_fiscal.document, criada pelo l10n_br_account
        via _inherits: sem o módulo fiscal (o
        l10n_br_account_payment_order não depende dele) nada é informado e o
        CNAB continua funcionando com os campos vazios. A presença é verificada
        no registry (e não em ir.module.module) para não consultar o banco a
        cada linha.
        """
        self.ensure_one()
        if "fiscal_document_id" not in self.move_id._fields:
            return {}
        # O l10n_br_account vincula (via _inherits) o account.move ao
        # l10n_br_fiscal.document onde estão a Chave do DF-e e os totais de
        # IBS/CBS. São usados os totais do Documento porque as parcelas
        # (linhas de vencimento) não possuem os valores de IBS/CBS.
        fiscal_document = self.move_id.fiscal_document_id
        # Os campos de IBS/CBS são do l10n_br_fiscal: se ele for anterior a eles
        # o CNAB segue com os campos vazios em vez de dar AttributeError.
        if not fiscal_document or "amount_ibs_value" not in fiscal_document._fields:
            return {}
        vals = {}
        if fiscal_document.document_key:
            vals["l10n_br_document_key"] = fiscal_document.document_key
        # O CBS/IBS Informado é do TÍTULO (e não do Documento Fiscal), veja
        # _split_payment_apportionment_values
        (
            vals["l10n_br_ibs_value"],
            vals["l10n_br_cbs_value"],
        ) = self._split_payment_apportionment_values(
            fiscal_document.amount_ibs_value, fiscal_document.amount_cbs_value
        )
        return vals

    def _split_payment_apportionment_values(self, total_ibs_value, total_cbs_value):
        """Rateia o IBS/CBS do Documento Fiscal entre as parcelas do título.

        O CBS/IBS Informado (campos X102/X103 do Segmento X-03) é do TÍTULO e
        não do Documento Fiscal: em fatura com mais de uma parcela cada boleto
        leva a MESMA Chave do DF-e com o tributo da sua parcela, porque o CBS e
        o IBS informados (separados ou somados) não podem ser superiores ao
        valor nominal do título - código 'X1' do Layout Padrão Febraban 240
        posições V11.0. O rateio é
        linear pelo valor das parcelas e, quando a parcela já tiver recebimento
        parcial, o tributo é reduzido na mesma proporção do residual (que é o
        valor do título informado no arquivo). As n-1 primeiras parcelas ficam
        com o valor arredondado e a ÚLTIMA com a diferença das anteriores, para
        a soma dos títulos fechar o que cabe às parcelas informadas.
        """
        installments = self._split_payment_installments()
        total_installments = sum(installments.mapped("amount_currency"))
        if not total_installments:
            # Sem parcelas/valores não há o que ratear: o tributo do Documento
            # Fiscal fica no título inteiro
            return total_ibs_value, total_cbs_value
        # O valor do título no arquivo é o residual da parcela (veja
        # account_payment_order: amount_residual_currency)
        proportions = [
            installment.amount_residual_currency / total_installments
            for installment in installments
        ]
        informed_positions = [
            position for position, proportion in enumerate(proportions) if proportion
        ]
        if not informed_positions:
            # Todos os títulos já recebidos: não há tributo a informar
            return 0.0, 0.0
        apportioned_ibs = [
            self.currency_id.round(total_ibs_value * proportion)
            for proportion in proportions
        ]
        apportioned_cbs = [
            self.currency_id.round(total_cbs_value * proportion)
            for proportion in proportions
        ]
        position = installments.ids.index(self.id)
        if position == informed_positions[-1]:
            # A última parcela informada fica com a diferença do arredondamento
            # das parcelas anteriores
            apportioned_ibs[position] = total_ibs_value * sum(proportions) - sum(
                apportioned_ibs[:position]
            )
            apportioned_cbs[position] = total_cbs_value * sum(proportions) - sum(
                apportioned_cbs[:position]
            )
        return apportioned_ibs[position], apportioned_cbs[position]

    def _split_payment_installments(self):
        """Parcelas (linhas de vencimento) do título a que a linha pertence."""
        installments = self.move_id.line_ids.filtered(
            lambda line: line.account_id.account_type
            in ("asset_receivable", "liability_payable")
        )
        return installments.sorted("date_maturity")

    def create_payment_line_from_move_line(self, payment_order):
        """
        Altera estado do cnab para adicionado a ordem
        :param payment_order:
        :return:
        """
        for record in self:
            cnab_state = "added"
            if record.reconciled:
                cnab_state = "added_paid"

            record.cnab_state = cnab_state

        return super().create_payment_line_from_move_line(payment_order)

    def generate_boleto(self, validate=True):
        raise NotImplementedError

    def write(self, values):
        """
        Sobrescrita do método Write. Não deve ser possível voltar o cnab_state
        ou a situacao_pagamento para um estado anterior
        :param values:
        :return:
        """
        for record in self:
            cnab_state = values.get("cnab_state")

            if cnab_state and (
                record.cnab_state == "done"
                or (
                    record.cnab_state in ["accepted", "accepted_hml"]
                    and cnab_state not in ["accepted", "accepted_hml", "done"]
                )
            ):
                values.pop("cnab_state", False)

            if record.payment_situation not in ["inicial", "aberta"]:
                values.pop("payment_situation", False)

        return super().write(values)

    def get_balance(self):
        """
        Return the balance of any set of move lines.

        Not to be confused with the 'balance' field on this model, which
        returns the account balance that the move line applies to.
        """
        total = 0.0
        for line in self:
            total += (line.debit or 0.0) - (line.credit or 0.0)
        return total

    @api.depends("own_number")
    def _compute_own_number_without_zfill(self):
        """
        No arquivo de retorno do CNAB o campo pode ter um tamanho
        diferente, o tamanho do campo é preenchido na totalidade
        com zeros a esquerda, e no odoo o tamanho do sequencial pode
        estar diferente
        ex.: retorno cnab 0000000000000201 own_number 0000000201

        O campo own_number_without_zfill foi a forma que encontrei
        para poder fazer um search o nosso_numero_cnab_retorno.lstrip("0") e
        ter algo:
        ex.:
        arquivo retorno cnab 201 own_number_without_zfill 201

        É usado o lstrip() para manter os zeros a direita, exemplo:
            VALOR '0000000090'
            | strip | rstrip | lstrip | 9 000000009 90

            Valor '00000000201'
            | strip | rstrip | lstrip | 201 00000000201 201

        :return: Valor sem os zeros a esquerda
        """
        for record in self:
            if record.own_number:
                record.own_number_without_zfill = record.own_number.lstrip("0")

    @api.depends("payment_mode_id")
    def _compute_journal_payment_mode(self):
        for record in self:
            if record.payment_mode_id:
                # CNAB usa sempre a opção fixed_journal_id
                if record.payment_mode_id.fixed_journal_id:
                    record.journal_payment_mode_id = (
                        record.payment_mode_id.fixed_journal_id.id
                    )

    def reconcile(self):
        res = super().reconcile()
        for record in self:
            # Verificar Casos de CNAB
            if (
                record.payment_mode_id.payment_method_code in BR_CODES_PAYMENT_ORDER
                and record.payment_mode_id.payment_method_id.payment_type == "inbound"
            ):
                # Na importação do arquivo de retorno o metodo também é
                # chamado no caso do modulo l10n_br_account_payment_brcobranca
                # o contexto traz o campo 'file_name' que ao ser encontrado
                # ignora o envio de alterações CNAB, outros modulos precisam
                # validar isso
                # Caso de Não Pagamento já está criando um Pedido de Baixa
                if self.env.context.get("file_name") or self.env.context.get(
                    "not_payment"
                ):
                    continue
                if record.matched_credit_ids:
                    for line in record.matched_credit_ids:
                        if not line.already_send_cnab:
                            record.create_payment_outside_cnab(line.amount)
                            line.already_send_cnab = True

        return res


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    # Evita que uma conciliação parcial seja
    # considerada novamente em um pagamento
    already_send_cnab = fields.Boolean(string="Already send CNAB")
