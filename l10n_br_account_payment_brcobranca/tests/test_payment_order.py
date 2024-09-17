# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
from datetime import date, timedelta
from unittest import mock

from odoo.exceptions import UserError
from odoo.modules import get_resource_path
from odoo.tests import Form, SavepointCase, tagged

_module_ns = "odoo.addons.l10n_br_account_payment_brcobranca"
_provider_class_pay_order = (
    _module_ns + ".models.account_payment_order" + ".PaymentOrder"
)
_provider_class_acc_invoice = _module_ns + ".models.account_move" + ".AccountMove"


@tagged("post_install", "-at_install")
class TestPaymentOrder(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.register_payments_model = cls.env["account.payment.register"].with_context(
            active_model="account.move"
        )
        cls.payment_model = cls.env["account.payment"]
        cls.aml_cnab_change_model = cls.env["account.move.line.cnab.change"]

        # Get Invoice for test
        cls.invoice_unicred = cls.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_unicred_cnab400"
        )
        cls.invoice_cef = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_payment_order_cef_cnab240"
        )
        cls.partner_akretion = cls.env.ref("l10n_br_base.res_partner_akretion")
        # I validate invoice by creating on
        cls.invoice_cef.action_post()

        payment_order = cls.env["account.payment.order"].search(
            [("payment_mode_id", "=", cls.invoice_cef.payment_mode_id.id)]
        )
        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-1.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()

        # Journal
        cls.journal_cash = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.invoice_cef.company_id.id)],
            limit=1,
        )
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )

        cls.aml_to_change = cls.invoice_cef.financial_move_line_ids[0]
        cls.ctx_change_cnab = {
            "active_model": "account.move.line",
            "active_ids": [cls.aml_to_change.id],
        }

    def _run_boleto_remessa(self, invoice, boleto_file, remessa_file):
        # I validate invoice
        invoice.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(invoice.state, "posted")

        # Imprimir Boleto
        if os.environ.get("CI_NO_BRCOBRANCA"):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                boleto_file,
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_acc_invoice + "._get_brcobranca_boleto",
                    return_value=mocked_response,
                ):
                    invoice.view_boleto_pdf()
        else:
            invoice.view_boleto_pdf()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", invoice.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 2)

        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                remessa_file,
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_banco_brasil_cnab_400(self):
        """Teste Boleto e Remessa Banco do Brasil - CNAB 400"""
        invoice_bb_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_bb_cnab400"
        )
        self._run_boleto_remessa(
            invoice_bb_cnab_400, "boleto_teste_bb400.pdf", "teste_remessa_bb400.REM"
        )

    def test_banco_itau_cnab_400(self):
        """Teste Boleto e Remessa Banco Itau - CNAB 400"""
        invoice_itau_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_itau_cnab400"
        )
        self._run_boleto_remessa(
            invoice_itau_cnab_400,
            "boleto_teste_itau400.pdf",
            "teste_remessa_itau400.REM",
        )

    def test_banco_bradesco_cnab_400(self):
        """Teste Boleto e Remessa Banco Bradesco - CNAB 400"""
        invoice_bradesco_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order"
        )
        self._run_boleto_remessa(
            invoice_bradesco_cnab_400,
            "boleto_teste_bradesco400.pdf",
            "teste_remessa_bradesco400.REM",
        )

    def test_banco_unicred_cnab_400(self):
        """Teste Boleto e Remessa Banco Unicred - CNAB 400"""
        invoice_unicred_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_unicred_cnab400"
        )
        self._run_boleto_remessa(
            invoice_unicred_cnab_400,
            "boleto_teste_unicred400.pdf",
            "teste_remessa-unicred_400-1.REM",
        )

    def test_banco_sicred_cnab_240(self):
        """Teste Boleto e Remessa Banco SICREDI - CNAB 240"""
        invoice_sicred_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_sicredi_cnab240"
        )

        self._run_boleto_remessa(
            invoice_sicred_cnab_240,
            "boleto_teste_sicredi_cnab240.pdf",
            "teste_remessa_sicredi240.REM",
        )

    def test_banco_ailos_cnab_240(self):
        """Teste Boleto e Remessa Banco AILOS - CNAB 240"""
        invoice_ailos_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_ailos_cnab240"
        )
        self._run_boleto_remessa(
            invoice_ailos_cnab_240,
            "boleto_teste_ailos_cnab240.pdf",
            "teste_remessa_ailos240.REM",
        )

    def test_banco_santander_cnab_400(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 400"""
        invoice_santander_cnab_400 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_santander_cnab400"
        )
        self._run_boleto_remessa(
            invoice_santander_cnab_400,
            "boleto_teste_santander400.pdf",
            "teste_remessa_santander400.REM",
        )

    def test_banco_santander_cnab_240(self):
        """Teste Boleto e Remessa Banco Santander - CNAB 240"""
        invoice_santander_cnab_240 = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_santander_cnab240"
        )
        self._run_boleto_remessa(
            invoice_santander_cnab_240,
            "boleto_teste_santander240.pdf",
            "teste_remessa_santander240.REM",
        )

    def test_bank_cnab_not_implement_brcobranca(self):
        """Test Bank CNAB not implemented in BRCobranca."""
        invoice = self.env.ref(
            "l10n_br_account_payment_order.demo_invoice_payment_order_itau_cnab240"
        )
        # I validate invoice
        invoice.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(invoice.state, "posted")
        # O Banco Itau CNAB 240 não está implementado no BRCobranca
        # por isso deve gerar erro.
        with self.assertRaises(UserError):
            invoice.view_boleto_pdf()

    def test_payment_order_invoice_cancel_process(self):
        """Test Payment Order and Invoice Cancel process."""

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        self.invoice_cef.button_cancel()

        # Caso de Ordem de Pagamento já confirmado a Linha
        # e a account.move não pode ser apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 2)
        # A partir da v13 as account.move.line relacionadas
        # continuam exisitindo
        self.assertEqual(len(self.invoice_cef.line_ids), 3)
        self.assertEqual(len(self.invoice_cef.invoice_line_ids), 1)

        # Criação do Pedido de Baixa
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )

        for line in payment_order.payment_line_ids:
            # Caso de Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )

    def test_payment_outside_cnab_writeoff_and_change_tittle_value(self):
        """
        Caso de Pagamento com CNAB já iniciado sendo necessário fazer a Baixa
        de uma Parcela e a Alteração de Valor de Titulo por pagto parcial.
        """

        payment = (
            self.env["account.payment"]
            .with_context(
                active_model="account.move",
                active_ids=self.invoice_cef.ids,
            )
            .create(
                {
                    "payment_type": "inbound",
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "partner_type": "customer",
                    "partner_id": self.partner_akretion.id,
                    "amount": 600,
                    "journal_id": self.journal_cash.id,
                }
            )
        )
        payment.action_post()

        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            if line.amount_currency == 300:
                # Caso de Baixa do Titulo
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    line.order_id.cnab_config_id.write_off_code_id.name,
                )
            else:
                # Caso de alteração do valor do titulo por pagamento parcial
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    line.order_id.cnab_config_id.change_title_value_code_id.name,
                )
                self.assertEqual(
                    line.move_line_id.amount_residual, line.amount_currency
                )

    def test_cnab_change_due_date(self):
        """
        Test CNAB Change Due Date
        """

        dict_change_due_date = {
            "change_type": "change_date_maturity",
        }
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create(dict_change_due_date)
        # Teste alteração com a mesma data não permitido
        # with self.assertRaises(UserError):
        #    aml_cnab_change.doit()
        # TODO ao rodar 2 vezes o metodo doit por algum motivo, ainda desconhecido,
        #  no teste o campo company_id na Order de Debito vem False, o que causa o
        #  erro abaixo:
        #  ###
        #  odoo.exceptions.UserError: Incompatible companies on records:
        #  - 'P00228' belongs to company False and 'Journal Item' (move_line_id:
        #  'Teste Caixa Economica Federal CNAB240 Teste Caixa Economica Federal CNAB240'
        #  ) belongs to another company.
        #  ###
        #  Porém esse campo é um related do payment_mode_id
        #  https://github.com/OCA/bank-payment/blob/14.0/
        #  account_payment_order/models/account_payment_order.py#L42
        #  e ao verificar no metodo que busca ou cria uma nova Ordem de Debito
        #  https://github.com/OCA/l10n-brazil/blob/14.0/
        #  l10n_br_account_payment_order/models/l10n_br_cnab_change_methods.py#L67
        #  é possível validar que o payment_mode_id está preechido:
        #  print('PAYMENT ORDER =====', payorder, payorder.name,
        #  payorder.payment_mode_id.name, payorder.payment_mode_id.company_id.name,
        #  payorder.company_id.name)
        #  PAYMENT ORDER ===== account.payment.order(139,) PAY0139
        #  Cobrança Caixa Economica Federal 240 Sua Empresa
        #  False

        new_date = date.today() + timedelta(days=30)

        dict_change_due_date.update({"date_maturity": new_date})
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create(dict_change_due_date)

        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.change_maturity_date_code_id.name,
            )

        # Open payment order
        payment_order.draft2open()
        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-2-data_venc.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_protest(self):
        """
        Test CNAB Protesto
        """
        # Protesto
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create({"change_type": "protest_tittle"})
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.protest_title_code_id.name,
            )
        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-3-protesto.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_suspend_protest_and_keep_wallet(self):
        """
        Test CNAB Suspend Protest and Keep Wallet
        """
        # Suspender Protesto e manter em carteira
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create({"change_type": "suspend_protest_keep_wallet"})
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )

        suspend_protest_keep_wallet_code = (
            self.aml_to_change.cnab_config_id.suspend_protest_keep_wallet_code_id
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                suspend_protest_keep_wallet_code.name,
            )
        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-4-sust_prot_mant_carteira.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_grant_rebate(self):
        """
        Test CNAB Grant Rebate
        """
        # Caso Conceder Abatimento
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create(
            {
                "change_type": "grant_rebate",
                "rebate_value": 10.0,
            }
        )
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.grant_rebate_code_id.name,
            )
            self.assertEqual(line.rebate_value, 10.0)

        # Open payment order
        payment_order.draft2open()
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.grant_rebate_code_id.name,
            )
            self.assertEqual(line.rebate_value, 10.0)

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-5-conceder_abatimento.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_cancel_rebate(self):
        """
        Test CNAB Cancel Rebate
        """
        # Caso Cancelar Abatimento
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create({"change_type": "cancel_rebate"})
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.cancel_rebate_code_id.name,
            )

        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-6-cancelar_abatimento.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_grant_discount(self):
        """
        Test CNAB Grant Discount
        """
        # Caso Conceder Desconto
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create(
            {
                "change_type": "grant_discount",
                "discount_value": 10.0,
            }
        )
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.grant_discount_code_id.name,
            )
            self.assertEqual(line.discount_value, 10.0)

        # Open payment order
        payment_order.draft2open()
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.grant_discount_code_id.name,
            )
            self.assertEqual(line.discount_value, 10.0)

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-7-conceder_desconto.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def test_cnab_cancel_discount(self):
        """
        Test CNAB Cancel Discount
        """
        # Caso Cancelar discount
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create({"change_type": "cancel_discount"})
        aml_cnab_change.doit()
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.cancel_discount_code_id.name,
            )

        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-8-cancelar_desconto.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

        # Suspender Protesto e dar Baixa
        # TODO: Especificar melhor esse caso

    def test_cnab_change_method_not_payment(self):
        """
        Test CNAB Change Method Not Payment
        """
        aml_cnab_change = self.aml_cnab_change_model.with_context(
            **self.ctx_change_cnab
        ).create({"change_type": "not_payment"})
        aml_cnab_change.doit()
        self.assertEqual(self.aml_to_change.payment_situation, "nao_pagamento")
        self.assertEqual(self.aml_to_change.cnab_state, "done")
        self.assertEqual(self.aml_to_change.reconciled, True)
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            # Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )

    def test_payment(self):
        """
        Caso de Pagamento com CNAB
        """
        self.partner_akretion = self.env.ref("l10n_br_base.res_partner_akretion")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        # Open payment order
        payment_order.action_cancel()
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-1.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice_cef.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 300 instead of 500
        payment_register.amount = 100
        payment_register.save()._create_payments()

        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )

        for line in payment_order.payment_line_ids:
            # Caso de alteração do valor do titulo por pagamento parcial
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.change_title_value_code_id.name,
            )
            self.assertEqual(line.move_line_id.amount_residual, line.amount_currency)

        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-9-alt_valor_titulo.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.invoice_cef.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 300 instead of 500
        payment_register.amount = 50
        payment_register.save()._create_payments()

        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            # Caso de alteração do valor do titulo por pagamento parcial
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.change_title_value_code_id.name,
            )
            self.assertEqual(line.move_line_id.amount_residual, line.amount_currency)

        # Open payment order
        payment_order.draft2open()

        # Verifica se deve testar com o mock
        if os.environ.get("CI_NO_BRCOBRANCA"):
            # Generate
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                "teste_remessa-cef_240-10-alt_valor_titulo.REM",
            )
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_pay_order + "._get_brcobranca_remessa",
                    return_value=mocked_response,
                ):
                    payment_order.open2generated()
        else:
            payment_order.open2generated()

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

        payment = (
            self.env["account.payment"]
            .with_context(
                active_model="account.move",
                active_ids=self.invoice_cef.ids,
            )
            .create(
                {
                    "payment_type": "inbound",
                    "payment_method_id": self.env.ref(
                        "account.account_payment_method_manual_in"
                    ).id,
                    "partner_type": "customer",
                    "partner_id": self.partner_akretion.id,
                    "amount": 150,
                    "journal_id": self.journal_cash.id,
                }
            )
        )
        payment.action_post()

        # Ordem de PAgto com alterações
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id),
                ("state", "=", "draft"),
            ]
        )
        for line in payment_order.payment_line_ids:
            # Baixa do Titulo
            self.assertEqual(
                line.instruction_move_code_id.name,
                line.order_id.cnab_config_id.write_off_code_id.name,
            )
            # TODO: Pedido de Baixa está indo com o valor inicial deveria ser
            #  o ultimo valor enviado ? Já que é um Pedido de Baixa o Banco
            #  validaria essas atualizações ?
            #  l.move_line_id.amount_residual = 0.0
            #  l.amount_currency = 300
            # self.assertEqual(
            #    l.move_line_id.amount_residual,
            #    l.amount_currency)
