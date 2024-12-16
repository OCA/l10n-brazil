# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import os
from unittest import mock

from odoo.modules import get_resource_path
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_account_payment_order.tests.test_base_class import (
    TestL10nBrAccountPaymentOder,
)

_module_ns = "odoo.addons.l10n_br_account_payment_brcobranca"
_provider_class_pay_order = (
    _module_ns + ".models.account_payment_order" + ".PaymentOrder"
)
_provider_class_cnab_parser = (
    _module_ns + ".parser.cnab_file_parser" + ".CNABFileParser"
)
_provider_class_acc_invoice = _module_ns + ".models.account_move" + ".AccountMove"


@tagged("post_install", "-at_install")
class TestBrAccountPaymentOderCommon(TestL10nBrAccountPaymentOder):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def _check_mocked_method(self, object_to_test, test_file, method_name):
        method_to_check = getattr(object_to_test, method_name)
        if os.environ.get("CI_NO_BRCOBRANCA"):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                test_file,
            )
            get_brcobranca_method = "._get_brcobranca_boleto"
            if method_name == "open2generated":
                get_brcobranca_method = "._get_brcobranca_remessa"
            with open(file_name, "rb") as f:
                mocked_response = f.read()
                with mock.patch(
                    _provider_class_acc_invoice + get_brcobranca_method,
                    return_value=mocked_response,
                ):
                    method_to_check()
        else:
            method_to_check()

    def _run_remessa(
        self, invoice, remessa_file, code_to_check=False, check_amount=False
    ):
        payment_order = self.env["account.payment.order"].search(
            [
                ("payment_mode_id", "=", invoice.payment_mode_id.id),
                ("state", "in", ("draft", "cancel")),
            ]
        )
        # Open payment order
        payment_order.draft2open()

        if code_to_check:
            for line in payment_order.payment_line_ids:
                # Caso de alteração do valor do titulo por pagamento parcial
                self.assertEqual(
                    line.instruction_move_code_id.name,
                    code_to_check.name,
                )
                if check_amount:
                    self.assertEqual(
                        line.move_line_id.amount_residual, line.amount_currency
                    )

        # Verifica se deve testar com o mock
        self._check_mocked_method(payment_order, remessa_file, "open2generated")

        # Confirm Upload
        payment_order.generated2uploaded()
        self.assertEqual(payment_order.state, "uploaded")

    def _run_boleto_remessa(self, invoice, boleto_file, remessa_file):
        # I validate invoice
        invoice.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(invoice.state, "posted")

        # Imprimir Boleto
        self._check_mocked_method(invoice, boleto_file, "view_boleto_pdf")

        self._run_remessa(invoice, remessa_file)

    def _make_payment(self, invoice, value):
        journal_cash = self.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", invoice.company_id.id)],
            limit=1,
        )

        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
        )
        payment_register.journal_id = journal_cash
        payment_register.payment_method_line_id = (
            journal_cash._get_available_payment_method_lines("inbound").filtered(
                lambda x: x.code == "manual"
            )
        )

        # Perform the partial payment by setting the amount at 300 instead of 500
        payment_register.amount = value
        payment_register.save()._create_payments()

    def _import_file(self, file_name, journal):
        """import a file using the wizard
        return the create account.bank.statement object
        """
        with open(file_name, "rb") as f:
            content = f.read()
            self.wizard = self.env["credit.statement.import"].create(
                {
                    "journal_id": journal.id,
                    "input_statement": base64.b64encode(content),
                    "file_name": os.path.basename(file_name),
                }
            )
            action = self.wizard.import_statement()
            log_view_ref = self.ref(
                "l10n_br_account_payment_order.l10n_br_cnab_return_log_form_view"
            )
            if action["views"] == [(log_view_ref, "form")]:
                # Se não for um codigo cnab de liquidação retorna
                # apenas o LOG criado.
                return self.env["l10n_br_cnab.return.log"].browse(action["res_id"])
            else:
                # Se for um codigo cnab de liquidação retorna
                # as account.move criadas.
                return self.env["account.move"].browse(action["res_id"])

    def _run_import_return_file(self, mocked_response, test_file, journal):
        with mock.patch(
            _provider_class_cnab_parser + "._get_brcobranca_retorno",
            return_value=mocked_response,
        ):
            file_name = get_resource_path(
                "l10n_br_account_payment_brcobranca",
                "tests",
                "data",
                test_file,
            )

            # Se for um codigo cnab de liquidação retorna as account.move criadas
            return self._import_file(file_name, journal)
