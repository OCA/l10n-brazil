# Copyright 2026-TODAY  KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDocumentRelated(TransactionCase):
    def test_check_cnpj_cpf(self):
        """create() must not raise: document.related has no vat field."""
        record = self.env["l10n_br_fiscal.document.related"].create(
            {
                "cnpj_cpf": "38425497000162",
                "cpfcnpj_type": "cnpj",
            }
        )
        self.assertEqual(record.cnpj_cpf, "38425497000162")

    def test_onchange_mask_cnpj_cpf(self):
        """the onchange must not raise, and must format the stored cnpj_cpf."""
        record = self.env["l10n_br_fiscal.document.related"].new(
            {
                "cnpj_cpf": "38425497000162",
                "cpfcnpj_type": "cnpj",
            }
        )
        record._onchange_mask_cnpj_cpf()
        self.assertEqual(record.cnpj_cpf, "38.425.497/0001-62")
