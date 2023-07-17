import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPayments(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_valid_boleto(self):

        boleto_input = "75691 3242101046.963706 00630.730018-8.94070000045000"
        inst_boleto = self.env["l10n_br.payment.instrument"].create(
            {
                "instrument_type": "boleto",
                "boleto_barcode_input": boleto_input,
            }
        )
        self.assertEqual(inst_boleto.boleto_barcode_input, boleto_input)
        self.assertEqual(
            inst_boleto.boleto_barcode_input_normalized,
            "75691324210104696370600630730018894070000045000",
        )
        self.assertEqual(
            inst_boleto.boleto_barcode, "75698940700000450001324201046963700063073001"
        )
        self.assertEqual(
            inst_boleto.boleto_digitable_line,
            "75691.32421 01046.963706 00630.730018 8 94070000045000",
        )

        sicoob_bank_id = self.env.ref("l10n_br_base.res_bank_756")
        self.assertEqual(inst_boleto.boleto_bank_id.id, sicoob_bank_id.id)

        self.assertEqual(inst_boleto.boleto_due, datetime.date(2023, 7, 10))
        self.assertEqual(inst_boleto.name, "Boleto 756989407000004500013242010469...")
        self.assertEqual(inst_boleto.boleto_amount, 450.00)

    def test_invalid_boleto(self):
        # this is not a correct input, it has too many digits.
        boleto_input = "99975691.32421 01046.963706 00630.730018 8 94070000045000"
        with self.assertRaises(ValidationError):
            self.env["l10n_br.payment.instrument"].create(
                {
                    "instrument_type": "boleto",
                    "boleto_barcode_input": boleto_input,
                }
            )

    def test_blank_barcode_boleto(self):
        with self.assertRaises(ValidationError):
            self.env["l10n_br.payment.instrument"].create(
                {
                    "instrument_type": "boleto",
                    "boleto_barcode_input": "",
                }
            )

    def test_valid_qrcode_pix(self):
        pix_string = (
            "00020126460014br.gov.bcb.pix0111999955559990209PIX TESTE"
            "520400005303986540410005802BR5913FULANO DE TAL6006Cidade"
            "6213050912345678963042423"
        )
        inst_pix = self.env["l10n_br.payment.instrument"].create(
            {
                "instrument_type": "pix_qrcode",
                "pix_qrcode_string": pix_string,
            }
        )
        self.assertEqual(inst_pix.pix_qrcode_string, pix_string)
        self.assertEqual(
            inst_pix.pix_qrcode_key,
            "99995555999",
        )
        self.assertEqual(
            inst_pix.pix_qrcode_txid,
            "123456789",
        )
        self.assertEqual(inst_pix.name, "Pix 00020126460014br.gov.bcb.pix01...")

    def test_invalid_qrcode_pix(self):
        pix_string = "pix12345789souumqrcodinvalido"
        with self.assertRaises(ValidationError):
            self.env["l10n_br.payment.instrument"].create(
                {
                    "instrument_type": "pix_qrcode",
                    "pix_qrcode_string": pix_string,
                }
            )._compute_pix_data()

    def test_blank_qrcode_pix(self):
        with self.assertRaises(ValidationError):
            self.env["l10n_br.payment.instrument"].create(
                {
                    "instrument_type": "pix_qrcode",
                    "pix_qrcode_string": "",
                }
            )._compute_pix_data()
