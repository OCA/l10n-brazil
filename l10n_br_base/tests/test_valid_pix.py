# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger

from .tools import load_fixture_files


class ValidCreatePIXTest(TransactionCase):
    """Test if ValidationError is raised well during create({})"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fixture_files(
            cls.env,
            "l10n_br_base",
            file_names=[
                "l10n_br_base_demo.xml",
                "res_partner_pix_demo.xml",
            ],
        )
        cls.res_partner_pix_model = cls.env["res.partner.pix"]
        cls.partner_id = cls.env.ref("l10n_br_base.res_partner_amd")

    def test_invalid_pix_cnpj_too_big(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "cnpj_cpf",
            "key": "0296089500013199",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_cnpj_too_less(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "cnpj_cpf",
            "key": "950001319",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_cnpj_wrong_value(self):
        # Desabilitando a Validação do CPF_CNPJ porque mesmo
        # nesse caso a validação da Chave PIX deve ser feita.
        self.env["ir.config_parameter"].set_param(
            "l10n_br_base.disable_cpf_cnpj_validation", True
        )

        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "cnpj_cpf",
            "key": "12345897560234",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_phone_wrong_value(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "phone",
            "key": "1103252020",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_phone_wrong_country_code(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "phone",
            "key": "0119991123456789",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_email_wrong_value(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "email",
            "key": "teste#teste.com",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_email_too_long(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "email",
            "key": "toooooooolooooooooooongemaaaaaailllllll@teeeeeeeee"
            "eeeeeeeeeeeeeeeeeeeest.com.br",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_wrong_value(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "nmmnaasa-qwhjwqhjk-2112",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_wrong_blocks(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "123e4567-e12b-12d1-a456-426655-40000",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_wrong_hex(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "123*4567-e12b-12d1-a456-426655440000",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_wrong_block_sizes(self):
        """36 characters, 5 hexadecimal blocks, but not 8-4-4-4-12."""
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "123456789-abc-1234-abcd-123456789abc",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_not_hexadecimal_digit(self):
        """Python's int(block, 16) accepted an underscore between digits."""
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "123e4567-e12b-12d1-a456-4266_5440000",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_invalid_pix_EVP_without_hyphens_wrong_size(self):
        """Without hyphens, the key must still have 32 digits (31 here)."""
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "evp",
            "key": "0123456789abcdef0123456789abcde",
        }
        self.check_validation_error_on_create(pix_vals)

    def test_valid_pix_EVP_normalized(self):
        """32 hexadecimal digits in 8-4-4-4-12 blocks, stored in lower case,
        without spaces, and with the hyphens when typed without them."""
        for typed, stored in (
            (
                "12345678-abcd-1234-abcd-123456789abc",
                "12345678-abcd-1234-abcd-123456789abc",
            ),
            (
                " ABCDEF12-3456-7890-ABCD-EF1234567890 ",
                "abcdef12-3456-7890-abcd-ef1234567890",
            ),
            (
                "0123456789ABCDEF0123456789abcdef",
                "01234567-89ab-cdef-0123-456789abcdef",
            ),
        ):
            with self.subTest(typed=typed):
                pix = self.res_partner_pix_model.create(
                    {"partner_id": self.partner_id.id, "key_type": "evp", "key": typed}
                )
                self.assertEqual(pix.key, stored)
                pix.unlink()

    def check_validation_error_on_create(self, pix_vals):
        with self.assertRaises(ValidationError):
            self.res_partner_pix_model.with_context(tracking_disable=True).create(
                pix_vals
            )

    def test_write_several_pix_keys(self):
        """Writing on several keys at once (e.g. a mass edit) works."""
        keys = self.env.ref("l10n_br_base.res_partner_amd_pix_cnpj") | self.env.ref(
            "l10n_br_base.res_partner_amd_pix_phone"
        )
        keys.write({"sequence": 5})
        self.assertEqual(keys.mapped("sequence"), [5, 5])
        self.assertEqual(keys.mapped("key"), ["62228384000151", "+551144576060"])

    def test_write_key_on_several_pix_keys(self):
        """A new key is normalized for each record written."""
        other_partner = self.env["res.partner"].create({"name": "Other Pix Partner"})
        keys = self.env.ref(
            "l10n_br_base.res_partner_amd_pix_email"
        ) | self.res_partner_pix_model.create(
            {
                "partner_id": other_partner.id,
                "key_type": "email",
                "key": "other@example.com",
            }
        )
        keys.write({"key": "Pix.Key@Example.com"})
        self.assertEqual(
            keys.mapped("key"), ["pix.key@example.com", "pix.key@example.com"]
        )

    def test_repeated_pix_key(self):
        pix_vals = {
            "partner_id": self.partner_id.id,
            "key_type": "phone",
            "key": "+50372424737",
        }
        self.res_partner_pix_model.with_context(tracking_disable=True).create(pix_vals)
        with mute_logger("odoo.sql_db"):
            with self.assertRaisesRegex(IntegrityError, "partner_pix_key_unique"):
                self.res_partner_pix_model.with_context(tracking_disable=True).create(
                    pix_vals
                )
