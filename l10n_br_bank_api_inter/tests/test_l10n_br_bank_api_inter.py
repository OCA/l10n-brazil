# @ 2021 KMEE - www.kmee.com.br
# Ygor Carvalho <ygor.carvalho@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from unittest import mock

from odoo.tests import SavepointCase
from odoo.exceptions import UserError

mock_test_write_off = {
    "nossoNumero": "54687321546",
    "seuNumero": "5",
    "cnpjCpfSacado": "23130935000198",
    "nomeSacado": "KMEE INFORMATICA LTDA",
    "codigoBaixa": "APEDIDODOCLIENTE",
    "situacao": "BAIXADO",
    "dataPagtoBaixa": "02/01/2021",
    "dataVencimento": "31/01/2021",
    "valorNominal": 100.01,
    "telefone": "30909303",
    "email": "contato@kmee.com.br",
    "dataEmissao": "01/01/2021",
    "dataLimite": "08/01/2021",
    "linhaDigitavel": "07700000000000000000000000000000000000000010001",
    "valorJuros": 0.00,
    "valorMulta": 0.00,
    "desconto1": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "desconto2": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "desconto3": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "multa": {
        "codigo": "NAOTEMMULTA",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "mora": {
        "codigo": "ISENTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "valorAbatimento": 0.00,
}

mock_test_splip_query = {
    "nomeBeneficiario": "Sua Empresa",
    "cnpjCpfBeneficiario": "23130935000198",
    "tipoPessoaBeneficiario": "JURIDICA",
    "dataHoraSituacao": "01/01/2021 00:00",
    "codigoBarras": "07700000000000000000000000000000000000000000",
    "linhaDigitavel": "07700000000000000000000000000000000000000012345",
    "dataVencimento": "31/01/2021",
    "dataEmissao": "01/01/2021",
    "seuNumero": "1234567810",
    "valorNominal": 123.45,
    "nomePagador": "KMEE INFORMATICA LTDA",
    "emailPagador": "contato@kmee.com.br",
    "dddPagador": "11",
    "telefonePagador": "30909303",
    "tipoPessoaPagador": "JURIDICA",
    "cnpjCpfPagador": "23130935000198",
    "codigoEspecie": "OUTROS",
    "dataLimitePagamento": "28/02/2021",
    "valorAbatimento": 0.00,
    "situacao": "EMABERTO",
    "mensagem": {
        "linha1": "TEXTO 1"
    },
    "desconto1": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "desconto2": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "desconto3": {
        "codigo": "NAOTEMDESCONTO",
        "taxa": 0.00,
        "valor": 0.00,
    },
    "multa": {
        "codigo": "PERCENTUAL",
        "data": "2021-01-31",
        "taxa": 5.00,
        "valor": 0.00,
    },
    "mora": {
        "codigo": "TAXAMENSAL",
        "data": "2021-01-31",
        "taxa": 1.00,
        "valor": 0.00,
    }
}

_module_ns = "odoo.addons.l10n_br_bank_api_inter"
_provider_class_pay_order = (
    _module_ns + ".models.account_payment_order" + ".AccountPaymentOrder"
)
_provider_class_aml = (
    _module_ns + ".models.account_move_line" + ".AccountMoveLine"
)


class TestBankInter(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.invoice_kmee_01 = cls.env.ref(
            "l10n_br_bank_api_inter.demo_invoice_inter_api_1"
        )
        cls.invoice_kmee_02 = cls.env.ref(
            "l10n_br_bank_api_inter.demo_invoice_inter_api_2"
        )

    def test_principal_workflow(self):
        """
        Normal system workflow. Start with the creation of an Invoice, the generation
        of a Debit Order and the generation of the bill of exchange.
        """
        self.invoice_kmee_01.action_invoice_open()
        self.assertEqual(self.invoice_kmee_01.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_01.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        self.assertEqual(len(payment_order.bank_line_ids), 1)

        with mock.patch(
            _provider_class_pay_order + ".generate_payment_file",
            return_value=(False, False)
        ):
            payment_order.open2generated()

        payment_order.generated2uploaded()

    def test_principal_workflow_key_cert(self):
        """
        It follows the same line as the main flow addressed in the case of Test 00,
        with  the exception  that there is no  certificate or key registered in the
        system.
        """
        self.invoice_kmee_01.action_invoice_open()
        self.assertEqual(self.invoice_kmee_01.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_01.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        with self.assertRaises(UserError):
            payment_order.open2generated()

    # TODO: Esse caso de teste está com problema, pois com a validação de cancelar a
    #   Invoice apenas quando todas as AML estiverem canceladas, impede que ele continue
    #   Necessário ver uma forma de cancelar o AML para que ela passe.
    def test_cancel_invoice(self):
        """
        Cancel the Invoice and, at the same time, cancel the bank skip that is lin-
        ked to it.
        """
        self.invoice_kmee_02.action_invoice_open()
        self.assertEqual(self.invoice_kmee_02.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_02.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        self.assertEqual(len(payment_order.bank_line_ids), 1)

        with mock.patch(
                _provider_class_pay_order + ".generate_payment_file",
                return_value=(False, False)
        ):
            payment_order.open2generated()

        payment_order.generated2uploaded()

        with mock.patch(
            _provider_class_aml + ".drop_bank_slip",
            return_value=mock_test_write_off
        ):
            write_off = payment_order.move_ids.line_ids.drop_bank_slip()
            self.assertEqual(write_off["situacao"], "BAIXADO")

        self.invoice_kmee_02.action_invoice_cancel()
        self.assertEqual(self.invoice_kmee_02.state, "cancel")

    def test_cancel_invoice_wt_cancel_aml(self):
        """
        Try to cancel the invoice without cancel the slip bank.
        """
        self.invoice_kmee_02.action_invoice_open()
        self.assertEqual(self.invoice_kmee_02.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_02.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        self.assertEqual(len(payment_order.bank_line_ids), 1)

        with mock.patch(
                _provider_class_pay_order + ".generate_payment_file",
                return_value=(False, False)
        ):
            payment_order.open2generated()

        payment_order.generated2uploaded()

        with self.assertRaises(UserError):
            self.invoice_kmee_02.action_invoice_cancel()

    def test_see_pdf_without_slip(self):
        """
        Try to view the bills linked to the Invoice without it having been generated.
        """
        self.invoice_kmee_02.action_invoice_open()
        self.assertEqual(self.invoice_kmee_02.state, "open")

        with self.assertRaises(UserError):
            self.invoice_kmee_02.action_pdf_boleto()

    def test_write_off(self):
        """
        Write off the bill directly in the AML, but without canceling the Invoice.
        """
        self.invoice_kmee_01.action_invoice_open()
        self.assertEqual(self.invoice_kmee_01.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_01.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        self.assertEqual(len(payment_order.bank_line_ids), 1)

        with mock.patch(
            _provider_class_pay_order + ".generate_payment_file",
            return_value=(False, False)
        ):
            payment_order.open2generated()

        payment_order.generated2uploaded()

        with mock.patch(
            _provider_class_aml + ".drop_bank_slip",
            return_value=mock_test_write_off
        ):
            writeoff = payment_order.move_ids.line_ids.drop_bank_slip()
            self.assertEqual(writeoff["situacao"], "BAIXADO")

    def test_slip_query(self):
        """
        Returns the billet query following some parameters.
        """
        self.invoice_kmee_01.action_invoice_open()
        self.assertEqual(self.invoice_kmee_01.state, "open")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_kmee_01.payment_mode_id.id)]
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        payment_order.draft2open()
        self.assertEqual(len(payment_order.bank_line_ids), 1)

        with mock.patch(
                _provider_class_pay_order + ".generate_payment_file",
                return_value=(False, False)
        ):
            payment_order.open2generated()

        payment_order.generated2uploaded()

        with mock.patch(
                _provider_class_aml + ".search_bank_slip",
                return_value=mock_test_splip_query
        ):
            slip_query = payment_order.move_ids.line_ids.search_bank_slip()
            self.assertEqual(slip_query["situacao"], "EMABERTO")
