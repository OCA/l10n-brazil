# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.tests import TransactionCase


class TestNFCeFiscalDoc(TransactionCase):
    def setUp(self):
        super().setUp()

        self.document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")

    def test_compute_fiscal_document_fields(self):
        self.document_id.partner_id.is_anonymous_consumer = True
        self.document_id.partner_id.cnpj_cpf = False
        self.document_id.partner_shipping_id = self.document_id.partner_id

        self.document_id._compute_entrega_data()
        self.assertFalse(self.document_id.nfe40_entrega)

        self.document_id.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        self.document_id._compute_dest_data()
        self.assertFalse(self.document_id.nfe40_dest)

    def test_prepare_nfce_payment(self):
        self.document_id.nfe40_detPag = [
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": 1,
                },
            ),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": 2,
                },
            ),
        ]

        try:
            self.document_id._eletronic_document_send()
        except Exception:  # flake8: noqa: E722
            # we don't want to check if the document is sending correctly here
            pass

        others_pag = self.document_id.nfe40_detPag.filtered(
            lambda p: p.nfe40_tPag == "99"
        )
        self.assertTrue(all(pag.nfe40_xPag == "Outros" for pag in others_pag))
