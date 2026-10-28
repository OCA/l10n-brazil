# Copyright (C) 2020-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright (C) 2020-Today - KMEE (<http://kmee.com.br>).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from ..constants import get_boleto_especie_short_name
from .common import CNABTestCommon

# Chave do Documento Fiscal (DF-e) usada nos testes do Split Payment (IBS/CBS),
# veja https://github.com/OCA/l10n-brazil/issues/5146 . O DV é válido porque o
# l10n_br_fiscal valida a chave do Documento Fiscal (a chave do arquivo de
# retorno de exemplo do outro módulo, terminada em ...12345, não passaria).
SPLIT_PAYMENT_DOCUMENT_KEY = "35260647906085000135550010000012341000012341"


@tagged("post_install", "-at_install")
class TestPaymentOrderInbound(CNABTestCommon):
    def test_invoice_button_add_to_pay_order(self):
        """Test Invoice Button to Add to a payment order"""
        self.pay_mode_cef.auto_create_payment_order = False
        self._invoice_confirm_workflow(self.invoice_cef_240)
        self.invoice_cef_240.create_account_payment_line()
        self._get_draft_payment_order(self.invoice_cef_240)

    def test_post_multiple_invoices_load_cnab_info(self):
        """Post several invoices at once, mixing CNAB and non CNAB payment modes"""
        cnab_invoices = self.invoice_cef_240 | self.invoice_itau_400
        invoices = cnab_invoices | self.invoice_cheque | self.invoice_without_pay_mode
        invoices.action_post()
        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        for invoice in cnab_invoices:
            inv_number = invoice.get_invoice_fiscal_number().split("/")[-1]
            due_lines = invoice.due_line_ids
            self.assertEqual(len(due_lines), 2)
            for index, line in enumerate(due_lines):
                self.assertEqual(line.document_number, f"{inv_number}/{index + 1:02d}")
                self.assertTrue(line.own_number)
                self.assertEqual(
                    line.instruction_move_code_id,
                    invoice.cnab_config_id.sending_code_id,
                )
            payment_order = self._get_draft_payment_order(invoice)
            self.assertEqual(payment_order.payment_line_ids.move_line_id, due_lines)
        for invoice in self.invoice_cheque | self.invoice_without_pay_mode:
            self.assertFalse(any(invoice.due_line_ids.mapped("own_number")))

    def test_post_cnab_invoice_with_other_invoices(self):
        """Post a CNAB invoice together with invoices without payment mode"""
        other_invoices = (
            self.invoice_without_pay_mode | self.invoice_without_pay_mode.copy()
        )
        (self.invoice_cef_240 | other_invoices).action_post()
        inv_number = self.invoice_cef_240.get_invoice_fiscal_number().split("/")[-1]
        self.assertEqual(
            self.invoice_cef_240.due_line_ids.mapped("document_number"),
            [f"{inv_number}/01", f"{inv_number}/02"],
        )
        self.assertTrue(all(self.invoice_cef_240.due_line_ids.mapped("own_number")))
        self.assertFalse(any(other_invoices.due_line_ids.mapped("own_number")))

    def test_payment_order_import_wizard(self):
        """Test Payment Order Import Wizard"""
        self.pay_mode_cef.auto_create_payment_order = False
        self._invoice_confirm_workflow(self.invoice_cef_240)
        self.import_with_po_wizard(self.invoice_cef_240.payment_mode_id)

    def test_pay_order_inbound_cnab_workflow(self):
        """Test Payment Order Inbound CNAB workflow"""

        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(len(payment_order.payment_line_ids), 2)
        # Change status of Move to draft just to test
        self.invoice_cef_240.button_cancel()
        self.assertEqual(len(payment_order.payment_line_ids), 0)
        # TODO Na v13 ao cancelar uma invoice as linhas de lançamentos
        #  contabeis são mantidas, é preciso confirmar se em nenhum caso
        #  as linhas são apagadas para assim poder eliminar do Roadmap
        #  essa questão é os campos que foram sobreescritos no modulo
        #  para funcionar antes
        # Nesse caso a account.move deverá ter sido apagada
        # self.assertEqual(len(self.invoice_cef_240.line_ids), 0)

        self._invoice_confirm_workflow(self.invoice_cef_240)

        # Verificar os campos CNAB na account.move.line
        for line in self.invoice_cef_240.line_ids.filtered(
            lambda line: line.own_number
        ):
            assert (
                line.own_number
            ), "own_number field is not filled in created Move Line."
            assert (
                line.instruction_move_code_id
            ), "instruction_move_code_id field is not filled in created Move Line."
            # testar com a parcela 700
            if line.debit == 700.0:
                test_balance_value = line.get_balance()

        self.assertEqual(test_balance_value, 700.0, "Error with method get_balance()")

        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        for pay_line in payment_order.payment_line_ids:
            self.assertFalse(
                pay_line.amount_interest, "Error with Amout Interest field"
            )

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        self._run_payment_order_workflow(payment_order)

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Test Sending multiple CNAB Instruction Movements
        for change in self.changes_to_sending:
            self._send_new_cnab_instruction_code(
                self.invoice_cef_240,
                change.get("change_to_send"),
                change.get("code_to_check"),
            )

    def test_warning_when_cnab_config_dont_has_code(self):
        self._run_invoice_and_order_workflow(self.invoice_itau_400)
        aml_to_change = self.invoice_itau_400.due_line_ids[0]
        self.changes_to_sending += [
            {
                "change_to_send": "change_date_maturity",
                "test_dates_are_equals": True,
            },
            {
                "change_to_send": "change_discount_date",
                "test_dates_are_equals": True,
            },
            {
                "change_to_send": "change_discount_date",
            },
            {"change_to_send": "suspend_protest_keep_wallet"},
            {
                "change_to_send": "not_payment",
                "without_account": True,
            },
        ]

        for change in self.changes_to_sending:
            test_dates_are_equals = False
            if change.get("test_dates_are_equals"):
                test_dates_are_equals = True
            # Caso not_payment não tem Warning
            if change.get("change_to_send") == "not_payment":
                self.cnab_config_itau_400.write_off_code_id = False
                if change.get("without_account"):
                    self.cnab_config_itau_400.not_payment_account_id = False
            self._send_new_cnab_code(
                aml_to_change,
                change.get("change_to_send"),
                warning_error=True,
                test_dates_are_equals=test_dates_are_equals,
            )

    def test_cnab_change_specific_cases(self):
        self._run_invoice_and_order_workflow(self.invoice_ailos_240)
        changes_to_sending = [
            {
                "change_to_send": "change_discount_date",
                "test_dates_are_equals": True,
                "warning_error": True,
            },
            {
                "change_to_send": "change_discount_date",
            },
        ]
        for change in changes_to_sending:
            self._send_new_cnab_code(
                self.invoice_ailos_240.due_line_ids[0],
                change.get("change_to_send"),
                change.get("warning_error"),
                change.get("test_dates_are_equals"),
            )
            if not change.get("warning_error"):
                pay_order = self._get_draft_payment_order(self.invoice_ailos_240)
                self._run_payment_order_workflow(pay_order)

    def test_payment_outside_cnab_payment_order_draft(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Draft deve
        apagar as linhas de pagamentos.
        """

        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        # Caso a Ordem de Pagamento ainda não esteja Confirmada
        payment = self._make_payment(self.invoice_cef_240, 1000.0)

        self.assertAlmostEqual(payment.amount, 1000.0)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(self.invoice_cef_240.payment_state, "in_payment")
        # Linhas Apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 0)

    def test_payment_outside_cnab_payment_order_open(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Open deve
        gerar erro por ter uma Instrução CNAB a ser enviada.
        """
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        payment_order.draft2open()
        self.assertEqual(payment_order.state, "open")

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste de crição de Write Off e Alteração do Valor do
        # Titulo no caso de um pagamento parcial precisa ser feito no modulo
        # que implementa biblioteca a ser usada.
        with self.assertRaises(UserError):
            self._make_payment(
                self.invoice_cef_240, self.invoice_cef_240.amount_residual
            )

    def test_payment_by_assign_outstanding_credit(self):
        """
        Caso de Pagamento com CNAB usando o assign_outstanding_credit
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        self._make_payment(self.invoice_cef_240, 100)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(
            payment_order.cnab_config_id.change_title_value_code_id,
            payment_order.payment_line_ids.mapped("instruction_move_code_id"),
            "Payment Order with wrong instruction_move_code_id for Write Off",
        )

    def test_payment_inbound_payment_in_cash_full(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        # I totally pay the Invoice
        payment = self._make_payment(
            self.invoice_cef_240, self.invoice_cef_240.amount_residual
        )
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "in_payment",
            "Invoice is not in Paid state",
        )
        self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_payment_inbound_payment_in_cash_twice(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        payment = self._make_payment(self.invoice_cef_240, 300)
        self.assertEqual(len(payment), 1)

        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "partial",
            "Invoice is not in Partial state",
        )

        # I totally pay the Invoice
        payment = self._make_payment(
            self.invoice_cef_240, self.invoice_cef_240.amount_residual
        )
        self.assertEqual(len(payment), 1)
        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "in_payment",
            "Invoice is not in Paid state",
        )
        self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_payment_inbound_cancel_invoice_already_registred(self):
        """Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" after we cancel
        the invoice.
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        self.invoice_cef_240.button_cancel()
        self._check_order_with_write_off_code(self.invoice_cef_240)
        pay_order = self._get_draft_payment_order(self.invoice_cef_240)
        self._run_payment_order_workflow(pay_order)
        self.invoice_cef_240.unlink()

    def test_cancel_invoice_no_payment_mode_pay(self):
        """Test Pay Invoice without payment mode in cash"""
        self._invoice_confirm_workflow(self.invoice_without_pay_mode)
        self.assertEqual(self.invoice_without_pay_mode.state, "posted")
        payment = self._make_payment(
            self.invoice_without_pay_mode,
            self.invoice_without_pay_mode.amount_residual,
        )
        self.assertEqual(len(payment), 1)
        self.assertEqual(
            self.invoice_without_pay_mode.payment_state,
            "paid",
            "Invoice is not in Paid state",
        )

    def test_cancel_invoice_no_payment_mode_cancel(self):
        """Test Cancel Invoice Without Payment Mode"""
        self._invoice_confirm_workflow(self.invoice_without_pay_mode)
        self.invoice_without_pay_mode.button_cancel()
        self.assertEqual(self.invoice_without_pay_mode.state, "cancel")

    def test_get_boleto_especies_short_name(self):
        # TODO: deveria estar sendo chamado por algum método?
        #  Verificar ao mudar o campo o boleto Especie de Char para Objeto
        name = get_boleto_especie_short_name("01")
        self.assertEqual(name, "DM")
        # Teste de Não encontrado
        not_found = get_boleto_especie_short_name("18")
        self.assertFalse(not_found)

    def test_constrains_payment_mode(self):
        """Test account.payment.mode Constrains methods"""
        with self.assertRaises(ValidationError):
            self.pay_mode_cef.write(
                {
                    "group_lines": True,
                }
            )

    def test_cnab_config(self):
        """Test CNAB Config validations"""
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.cnab_sequence_id = self.cnab_seq_cef
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.own_number_sequence_id = self.own_number_seq_cef
        with self.assertRaises(ValidationError):
            self.cnab_config_cef.boleto_discount_perc = 101
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.boleto_wallet = False

    def test_payment_mode_without_payment_order(self):
        """Test Invoice when Payment Mode not generate Payment Order."""
        self._invoice_confirm_workflow(self.invoice_cheque)
        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_cheque.payment_mode_id.id),
            ]
        )
        self.assertEqual(len(payment_order), 0)

    def test_bra_number_constrains(self):
        """Test bra_number constrains."""
        with self.assertRaises(UserError):
            self.env["res.partner.bank"].create(
                {
                    "bank_id": self.env.ref("l10n_br_base.res_bank_033").id,
                    "partner_id": self.partner_a.id,
                    "bra_number": "12345",
                }
            )

    def _check_fiscal_document_link(self):
        """True quando existe a relação do account.move com o Documento Fiscal.

        Só o l10n_br_account cria essa relação (via _inherits) e ele não é
        dependência do l10n_br_account_payment_order.
        """
        return "fiscal_document_id" in self.env["account.move"]._fields

    def test_payment_line_split_payment_fields_without_fiscal(self):
        """Campos do Split Payment do IBS/CBS sem o fiscal instalado.

        Sem o l10n_br_account não existe a relação do account.move com o
        l10n_br_fiscal.document, então os campos l10n_br_ibs_value,
        l10n_br_cbs_value e l10n_br_document_key ficam vazios e o fluxo CNAB
        segue inalterado, veja https://github.com/OCA/l10n-brazil/issues/5146 .
        """
        if self._check_fiscal_document_link():
            self.skipTest("Test scenario without l10n_br_account installed.")
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertTrue(payment_order.payment_line_ids, "Payment Lines not created.")
        for line in payment_order.payment_line_ids:
            self.assertFalse(line.l10n_br_document_key)
            self.assertFalse(line.l10n_br_ibs_value)
            self.assertFalse(line.l10n_br_cbs_value)

    def test_payment_line_split_payment_fields_with_fiscal(self):
        """Campos do Split Payment do IBS/CBS com o Documento Fiscal presente.

        Quando existe a relação do account.move com o l10n_br_fiscal.document
        (criada pelo l10n_br_account via _inherits) a Chave do DF-e e os totais
        de IBS/CBS do Documento Fiscal passam para a linha de pagamento, veja
        https://github.com/OCA/l10n-brazil/issues/5146 . O CBS/IBS Informado é
        do título: em fatura com mais de uma parcela o valor é rateado entre
        elas, veja test_payment_line_split_payment_apportionment.
        """
        if not self._check_fiscal_document_link():
            self.skipTest("Test scenario requires l10n_br_account installed.")
        # O usuário do teste precisa do grupo fiscal para criar o Documento Fiscal
        self.env.user.groups_id |= self.env.ref("l10n_br_fiscal.group_user")
        invoice = self.invoice_cef_240
        fiscal_document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.env.ref(
                    "l10n_br_fiscal.document_55_serie_1"
                ).id,
                "partner_id": invoice.partner_id.id,
                "company_id": invoice.company_id.id,
                "document_key": SPLIT_PAYMENT_DOCUMENT_KEY,
            }
        )
        invoice.fiscal_document_id = fiscal_document
        # O Documento Fiscal do teste é criado sem itens, então os valores de
        # IBS/CBS são informados aqui (o workflow de confirmação da fatura cria
        # as linhas de pagamento, que são rateadas por esses valores - veja
        # test_payment_line_split_payment_apportionment)
        fiscal_document.write({"amount_ibs_value": 1.55, "amount_cbs_value": 0.55})
        self._invoice_confirm_workflow(invoice)
        self.assertAlmostEqual(fiscal_document.amount_ibs_value, 1.55, places=2)
        payment_order = self._get_draft_payment_order(invoice)
        self.assertTrue(payment_order.payment_line_ids, "Payment Lines not created.")
        payment_lines = payment_order.payment_line_ids
        for line in payment_lines:
            self.assertEqual(line.l10n_br_document_key, SPLIT_PAYMENT_DOCUMENT_KEY)
            # O CBS/IBS Informado é do TÍTULO: cada parcela leva a sua parte (e
            # não o total do Documento Fiscal)
            self.assertTrue(
                0 < line.l10n_br_ibs_value < fiscal_document.amount_ibs_value,
                f"ibs={line.l10n_br_ibs_value} doc={fiscal_document.amount_ibs_value} "
                f"installments={len(payment_lines)}",
            )
            self.assertTrue(
                0 < line.l10n_br_cbs_value < fiscal_document.amount_cbs_value,
                f"cbs={line.l10n_br_cbs_value} doc={fiscal_document.amount_cbs_value} "
                f"installments={len(payment_lines)}",
            )
        # A soma dos títulos fecha o total do Documento Fiscal
        self.assertAlmostEqual(
            sum(payment_lines.mapped("l10n_br_ibs_value")),
            fiscal_document.amount_ibs_value,
            places=2,
        )
        self.assertAlmostEqual(
            sum(payment_lines.mapped("l10n_br_cbs_value")),
            fiscal_document.amount_cbs_value,
            places=2,
        )

    def test_payment_line_split_payment_vals(self):
        """Dados do Split Payment que devem ser informados no arquivo CNAB.

        A decisão é da Configuração do CNAB e do Código de Movimento da linha:
        o Segmento X-03 acompanha a Entrada de Títulos e as Alterações, e não
        as Instruções ao Banco, veja
        https://github.com/OCA/l10n-brazil/issues/5146 . Os dados entram no
        dicionário do Boleto montado pelo `_prepare_boleto_line_vals`, que
        também é do módulo comum.
        """
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        line = payment_order.payment_line_ids[0]
        cnab_config = payment_order.payment_mode_id.cnab_config_id

        # A linha criada ao confirmar a fatura está na Entrada de Títulos e, sem
        # a marcação na Configuração CNAB, nada é informado
        self.assertEqual(line.instruction_move_code_id, cnab_config.sending_code_id)
        self.assertFalse(cnab_config.use_split_payment)
        self.assertFalse(line._prepare_split_payment_vals())

        # Com a marcação os dados vão na Entrada de Títulos e na Alteração do
        # Valor do Título, os dois eventos em que o Segmento X-03 é previsto
        cnab_config.use_split_payment = True
        line.write(
            {
                "l10n_br_document_key": SPLIT_PAYMENT_DOCUMENT_KEY,
                "l10n_br_ibs_value": 0.2,
                "l10n_br_cbs_value": 1.8,
            }
        )
        expected_vals = {
            "documento_fiscal": SPLIT_PAYMENT_DOCUMENT_KEY,
            "valor_ibs": 0.2,
            "valor_cbs": 1.8,
        }
        for code in (
            cnab_config.sending_code_id,
            cnab_config.change_title_value_code_id,
        ):
            line.instruction_move_code_id = code
            self.assertEqual(line._prepare_split_payment_vals(), expected_vals)

        # Nas Instruções ao Banco, como o Pedido de Baixa, o Segmento X-03 não é
        # previsto e o arquivo continua o mesmo
        line.instruction_move_code_id = cnab_config.write_off_code_id
        self.assertFalse(line._prepare_split_payment_vals())
        line.instruction_move_code_id = cnab_config.sending_code_id

        # O CBS e o IBS vão juntos, mesmo com um deles zerado, e a Chave do
        # Documento Fiscal é opcional no layout
        line.write(
            {
                "l10n_br_document_key": False,
                "l10n_br_ibs_value": 0.0,
                "l10n_br_cbs_value": 1.8,
            }
        )
        self.assertEqual(
            line._prepare_split_payment_vals(), {"valor_ibs": 0.0, "valor_cbs": 1.8}
        )

        # Sem dados do Split Payment no título nada é informado (o arquivo não
        # leva nem os valores zerados)
        line.write({"l10n_br_ibs_value": 0.0, "l10n_br_cbs_value": 0.0})
        self.assertFalse(line._prepare_split_payment_vals())

    def test_payment_line_split_payment_boleto_vals(self):
        """Dados do Split Payment no dicionário do Boleto (Remessa).

        O `_prepare_boleto_line_vals` é deste módulo e é o único lugar que monta
        o dicionário enviado ao módulo processador do CNAB: os dados do Split
        Payment entram nele com os nomes das chaves do
        Boleto_CNAB_API/BRCobranca (`documento_fiscal`, `valor_ibs` e
        `valor_cbs`), que geram o registro opcional Segmento X-03 da Remessa de
        Cobrança do Layout Padrão Febraban 240 posições V11.0, veja
        https://github.com/OCA/l10n-brazil/issues/5146 .
        """
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        line = payment_order.payment_line_ids[:1]
        cnab_config = payment_order.payment_mode_id.cnab_config_id
        # Dados do sacado usados no dicionário do Boleto
        line.partner_id.write(
            {
                "legal_name": "Partner A LTDA",
                "cnpj_cpf": "66.793.591/0001-00",
                "street_name": "Av. Paulista",
                "street_number": "1000",
                "district": "Bela Vista",
                "zip": "01310-100",
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
                "state_id": self.env.ref("base.state_br_sp").id,
            }
        )
        line.date = fields.Date.today()
        split_payment_keys = ("documento_fiscal", "valor_ibs", "valor_cbs")
        cnab_config.use_split_payment = True
        line.write(
            {
                "l10n_br_document_key": SPLIT_PAYMENT_DOCUMENT_KEY,
                "l10n_br_ibs_value": 0.2,
                "l10n_br_cbs_value": 1.8,
            }
        )
        boleto_vals = line._prepare_boleto_line_vals()
        self.assertEqual(
            {key: boleto_vals[key] for key in split_payment_keys},
            {
                "documento_fiscal": SPLIT_PAYMENT_DOCUMENT_KEY,
                "valor_ibs": 0.2,
                "valor_cbs": 1.8,
            },
        )

        # Com a opção desmarcada na Configuração do CNAB o dicionário continua
        # igual ao de antes do Split Payment
        cnab_config.use_split_payment = False
        self.assertFalse(
            set(split_payment_keys) & set(line._prepare_boleto_line_vals())
        )
        cnab_config.use_split_payment = True

        # Nas Instruções ao Banco, como o Pedido de Baixa, o Segmento X-03 não é
        # previsto e o dicionário também não leva os dados
        line.instruction_move_code_id = cnab_config.write_off_code_id
        self.assertFalse(
            set(split_payment_keys) & set(line._prepare_boleto_line_vals())
        )

    def test_payment_line_split_payment_apportionment(self):
        """Rateio do IBS/CBS do Documento Fiscal entre as parcelas do título.

        O CBS/IBS Informado é do TÍTULO e não do Documento Fiscal: cada boleto
        leva a mesma Chave do DF-e com o tributo da sua parcela - as n-1
        primeiras com o rateio arredondado e a ÚLTIMA com a diferença do total -
        porque a soma do CBS e do IBS não pode ser superior ao valor nominal do
        título, código 'X1' do Layout Padrão Febraban 240 posições V11.0, veja
        https://github.com/OCA/l10n-brazil/issues/5146 . A conta é testada sem o
        l10n_br_fiscal porque não depende dele (os totais do Documento Fiscal
        são informados por parâmetro).
        """
        self._invoice_confirm_workflow(self.invoice_cef_240)
        installments = self.invoice_cef_240.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        ).sorted("date_maturity")
        # O prazo de pagamento da fatura do teste é 30% no vencimento e o
        # restante depois, logo as parcelas tem valores diferentes
        self.assertEqual(len(installments), 2)
        self.assertNotEqual(
            installments[0].amount_currency, installments[1].amount_currency
        )
        total_ibs_value = 1.55
        total_cbs_value = 0.55
        apportionments = [
            installment._split_payment_apportionment_values(
                total_ibs_value, total_cbs_value
            )
            for installment in installments
        ]
        apportioned_ibs = [ibs_value for ibs_value, _cbs_value in apportionments]
        apportioned_cbs = [cbs_value for _ibs_value, cbs_value in apportionments]

        # Nenhum título leva o total do Documento Fiscal
        self.assertTrue(all(value < total_ibs_value for value in apportioned_ibs))
        self.assertTrue(all(value < total_cbs_value for value in apportioned_cbs))
        # A soma dos títulos fecha o total do Documento Fiscal (a última parcela
        # fica com a diferença do arredondamento das anteriores)
        self.assertAlmostEqual(sum(apportioned_ibs), total_ibs_value, places=2)
        self.assertAlmostEqual(sum(apportioned_cbs), total_cbs_value, places=2)
        # Cada parcela leva a parte proporcional ao seu valor
        total_installments = sum(installments.mapped("amount_currency"))
        proportional_ibs = installments[0].currency_id.round(
            total_ibs_value * installments[0].amount_currency / total_installments
        )
        proportional_cbs = installments[0].currency_id.round(
            total_cbs_value * installments[0].amount_currency / total_installments
        )
        self.assertEqual(apportioned_ibs[0], proportional_ibs)
        self.assertEqual(apportioned_cbs[0], proportional_cbs)
        self.assertEqual(apportioned_ibs[1], total_ibs_value - proportional_ibs)
        self.assertEqual(apportioned_cbs[1], total_cbs_value - proportional_cbs)

    def test_payment_line_split_payment_partial_payment(self):
        """Rateio reduz o tributo na proporção do recebimento parcial.

        O valor informado no arquivo é o valor do título, ou seja o residual da
        parcela (account_payment_order: amount_residual_currency): parcela com
        recebimento parcial leva o CBS/IBS reduzido na mesma proporção, para a
        soma do CBS e do IBS não passar do valor nominal do título - código 'X1'
        do Layout Padrão Febraban 240 posições V11.0, veja
        https://github.com/OCA/l10n-brazil/issues/5146 .
        """
        # O pagamento parcial é feito antes de criar a ordem de pagamento (senão
        # o módulo bloqueia: uma nova instrução CNAB só é possível depois de
        # enviar o arquivo ao banco, veja _check_cnab_instruction_to_be_send)
        self.pay_mode_cef.auto_create_payment_order = False
        self._invoice_confirm_workflow(self.invoice_cef_240)
        installments = self.invoice_cef_240.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        ).sorted("date_maturity")
        self.assertEqual(len(installments), 2)
        # Recebimento parcial de um dos títulos: o residual fica menor que o
        # valor nominal da parcela
        self._make_payment(self.invoice_cef_240, 100.0)
        installments.invalidate_recordset(
            ["amount_currency", "amount_residual", "amount_residual_currency"]
        )
        self.assertTrue(
            any(
                installment.amount_residual_currency < installment.amount_currency
                for installment in installments
            ),
            "Test scenario requires an installment with partial payment.",
        )
        total_ibs_value = 1.55
        total_cbs_value = 0.55
        # O valor do Documento Fiscal continua sendo a soma das parcelas
        total_installments = sum(installments.mapped("amount_currency"))
        proportions = [
            installment.amount_residual_currency / total_installments
            for installment in installments
        ]
        apportionments = [
            installment._split_payment_apportionment_values(
                total_ibs_value, total_cbs_value
            )
            for installment in installments
        ]

        # O total informado é proporcional ao que resta dos títulos (a parte já
        # recebida não é informada de novo)
        self.assertAlmostEqual(
            sum(ibs_value for ibs_value, _cbs_value in apportionments),
            total_ibs_value * sum(proportions),
            places=2,
        )
        self.assertAlmostEqual(
            sum(cbs_value for _ibs_value, cbs_value in apportionments),
            total_cbs_value * sum(proportions),
            places=2,
        )
        # Cada título leva o tributo na proporção do seu residual, sem passar do
        # valor do título
        for position, installment in enumerate(installments):
            ibs_value, cbs_value = apportionments[position]
            self.assertAlmostEqual(
                ibs_value, total_ibs_value * proportions[position], delta=0.01
            )
            self.assertAlmostEqual(
                cbs_value, total_cbs_value * proportions[position], delta=0.01
            )
            self.assertLessEqual(
                ibs_value + cbs_value, installment.amount_residual_currency
            )
