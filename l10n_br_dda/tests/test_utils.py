# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests.common import TransactionCase, tagged

from .. import utils


@tagged("post_install", "-at_install")
class TestUtils(TransactionCase):
    def test_normalize_cnpj_keeps_letters(self):
        self.assertEqual(utils.normalize_cnpj("12.abc.345/01de-35"), "12ABC34501DE35")
        self.assertEqual(utils.normalize_cnpj(None), "")
        self.assertEqual(utils.cnpj_root("12.ABC.345/01DE-35"), "12ABC345")
        self.assertEqual(utils.cnpj_root("291.250.832-01"), "")

    def test_normalize_document_number(self):
        cases = {
            "1234/1": "1234",
            "001234": "1234",
            "NF-1234/02": "1234",
            "1234": "1234",
            "": "",
            None: "",
            "000": "",
        }
        for raw, expected in cases.items():
            self.assertEqual(utils.normalize_document_number(raw), expected, raw)

    def test_normalize_digitable_line(self):
        self.assertEqual(
            utils.normalize_digitable_line("34191.09008 61207"), "341910900861207"
        )

    def test_to_date(self):
        self.assertEqual(utils.to_date("2026-10-26"), date(2026, 10, 26))
        self.assertIsNone(utils.to_date("0001-01-01"))
        self.assertIsNone(utils.to_date(date(1, 1, 1)))
        self.assertIsNone(utils.to_date("garbage"))

    def test_digitable_line_has_every_check_digit_right(self):
        line = utils.build_digitable_line("341", 1240.00, date(2026, 11, 5), "seed:1")
        self.assertEqual(len(line), 47)
        for start, end in ((0, 9), (10, 20), (21, 31)):
            field = line[start:end]
            self.assertEqual(int(line[end]), utils.dv_mod10(field))
        barcode = line[0:4] + line[33:47] + line[4:9] + line[10:20] + line[21:31]
        self.assertEqual(int(line[32]), utils.dv_mod11_barras(barcode))
        self.assertEqual(line[37:], "0000124000")
        self.assertEqual(line[33:37], str(utils.due_factor(date(2026, 11, 5))))
