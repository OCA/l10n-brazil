# Copyright (C) 2026 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPixQrCodeEmv(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brl = cls.env.ref("base.BRL")
        cls.brl.active = True
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "ZITRON BRASIL",
                "city": "INDAIATUBA",
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.bank_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "12345-6",
                "partner_id": cls.partner.id,
            }
        )
        cls.pix = cls.env["res.partner.pix"].create(
            {
                "partner_id": cls.partner.id,
                "partner_bank_id": cls.bank_account.id,
                "key_type": "cnpj_cpf",
                "key": "12.345.678/0001-95",
            }
        )
        cls.debtor = cls.env["res.partner"].create({"name": "Cliente"})

    def _qr_value(self, amount=745.10, comment=None):
        return self.bank_account._get_qr_vals(
            "emv_qr", amount, self.brl, self.debtor, comment, None
        )

    @staticmethod
    def _tlv(payload):
        """Walk the top level TLVs and return {tag: value}."""
        fields, index = {}, 0
        while index < len(payload):
            tag = payload[index : index + 2]
            length = int(payload[index + 2 : index + 4])
            fields[tag] = payload[index + 4 : index + 4 + length]
            index += 4 + length
        return fields

    def test_merchant_account_information_carries_the_pix_gui_and_key(self):
        fields = self._tlv(self._qr_value())
        self.assertEqual(fields["26"], "0014br.gov.bcb.pix011412345678000195")

    def test_payload_matches_a_known_br_code(self):
        """Payload checked field by field against the Central Bank BR Code. It is an
        anchor: any change of tag, order or length breaks here instead of in the bank
        app, where the only symptom is an unhelpful "invalid QR code"."""
        self.assertEqual(
            self._qr_value(),
            "00020101021226360014br.gov.bcb.pix0114123456780001955204000053039865406"
            "745.105802BR5913ZITRON BRASIL6010INDAIATUBA62070503***63040830",
        )

    def test_crc16_closes_over_the_whole_payload(self):
        payload = self._qr_value()
        self.assertEqual(
            payload[-4:],
            format(
                self.bank_account._get_crc16(bytes(payload[:-4], "utf-8")), "04x"
            ).upper(),
        )

    def test_reference_label_is_three_asterisks_when_there_is_no_txid(self):
        """Field 62 is required by the BR Code even without a transaction id."""
        fields = self._tlv(self._qr_value())
        self.assertEqual(fields["62"], "0503***")

    def test_reference_label_carries_the_communication_when_asked(self):
        self.bank_account.include_reference = True
        fields = self._tlv(self._qr_value(comment="NF 000123"))
        self.assertEqual(fields["62"], "0509NF 000123")

    def test_qr_setting_shows_for_brazilian_accounts(self):
        self.assertTrue(self.bank_account.display_qr_setting)

    def test_account_without_pix_key_reports_why(self):
        self.pix.unlink()
        self.assertIn(
            "no Pix key",
            self.bank_account._get_error_messages_for_qr(
                "emv_qr", self.debtor, self.brl
            ),
        )

    def test_currency_other_than_brl_is_refused(self):
        usd = self.env.ref("base.USD")
        self.assertIn(
            "only available in BRL",
            self.bank_account._get_error_messages_for_qr("emv_qr", self.debtor, usd),
        )

    def test_key_falls_back_to_the_partner_when_not_linked_to_the_account(self):
        """A company with a single key usually does not tie it to a bank account."""
        self.pix.partner_bank_id = False
        self.assertEqual(self.bank_account._get_pix_key(), "12345678000195")

    def test_non_brazilian_account_keeps_the_base_behaviour(self):
        foreign = self.env["res.partner"].create(
            {"name": "Foreign", "country_id": self.env.ref("base.us").id}
        )
        account = self.env["res.partner.bank"].create(
            {"acc_number": "US-1", "partner_id": foreign.id}
        )
        self.assertEqual(account._get_merchant_account_info(), (None, None))
        self.assertEqual(account._get_merchant_category_code(), "0000")
