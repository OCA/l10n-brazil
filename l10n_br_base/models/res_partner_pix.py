# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

import phonenumbers
from email_validator import EmailSyntaxError, validate_email

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..tools import check_cnpj_cpf

# EVP (Endereço Virtual de Pagamento, the random key): 32 hexadecimal digits in
# blocks of 8-4-4-4-12 separated by hyphens, the UUID format
EVP_PATTERN = re.compile(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")
EVP_DIGITS = re.compile(r"[0-9a-f]{32}")


class PartnerPix(models.Model):
    _name = "res.partner.pix"
    _description = "Brazilian instant payment ecosystem (Pix)"
    _order = "sequence, id"
    _rec_name = "key"

    _sql_constraints = [
        (
            "partner_pix_key_unique",
            "unique(key_type, key, partner_id)",
            "A Pix Key with this values already exists in this partner.",
        )
    ]

    KEY_TYPES = [
        ("cnpj_cpf", "CPF or CNPJ"),
        ("phone", "Phone Number"),
        ("email", "E-mail"),
        ("evp", "Random Key"),
    ]

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="cascade",
        required=True,
    )
    sequence = fields.Integer(default=10)
    key_type = fields.Selection(
        selection=KEY_TYPES,
        string="Type",
        required=True,
    )
    key = fields.Char(
        help="PIX Addressing key",
        required=True,
    )

    partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        string="Bank Account",
        domain="[('partner_id', '=', partner_id)]",
    )

    def _normalize_email(self, email):
        try:
            result = validate_email(
                email.lower(),
                check_deliverability=False,
            )
        except EmailSyntaxError as e:
            raise ValidationError(
                self.env._(
                    "%(email_strip)s is an invalid email", email_strip=email.strip()
                )
            ) from e
        normalized_email = result.local_part + "@" + result.domain
        if len(normalized_email) > 77:
            raise ValidationError(
                self.env._(
                    "The email is too long, "
                    "a maximum of 77 characters is allowed: %(email_strip)s",
                    email_strip=email.strip(),
                )
            ) from None
        return normalized_email

    def _normalize_phone(self, phone):
        try:
            phonenumber = phonenumbers.parse(phone, "BR")
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValidationError(
                self.env._(
                    "Unable to parse %(phone)s: %(str_e)s", phone=phone, str_e=repr(e)
                )
            ) from e
        if not phonenumbers.is_possible_number(phonenumber):
            raise ValidationError(
                self.env._(
                    "Impossible number %(phone)s: probably invalid number of digits.",
                    phone=phone,
                )
            ) from None
        if not phonenumbers.is_valid_number(phonenumber):
            raise ValidationError(
                self.env._(
                    "Invalid number %(phone)s: probably incorrect prefix.", phone=phone
                )
            ) from None
        phone = phonenumbers.format_number(
            phonenumber, phonenumbers.PhoneNumberFormat.E164
        )
        return phone

    def _normalize_cnpj_cpf(self, doc_number):
        check_cnpj_cpf(self.env, doc_number, self.env.ref("base.br"), True)
        return "".join(char for char in doc_number if char.isalnum())

    def _normalize_evp(self, key):
        # Like a UUID, the key is case insensitive (RFC 4122): stored in lower
        # case, so the same key cannot be registered twice. Typed without the
        # hyphens, it gets them.
        key = "".join(key.split()).lower()
        if EVP_DIGITS.fullmatch(key):
            key = "-".join((key[:8], key[8:12], key[12:16], key[16:20], key[20:]))
        if not EVP_PATTERN.fullmatch(key):
            raise ValidationError(
                self.env._(
                    "Invalid Random Key: %(key)s. Make sure the whole key was "
                    "copied. It must have exactly 36 characters (letters from a "
                    "to f, digits and hyphens). Example of the correct format: "
                    "12345678-abcd-1234-abcd-123456789abc",
                    key=key,
                )
            )
        return key

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.check_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self.check_vals(vals)
        return super().write(vals)

    def check_vals(self, vals):
        key_type = vals.get("key_type") or self.key_type
        key = vals.get("key") or self.key
        if not key or not key_type:
            return
        if key_type == "email":
            key = self._normalize_email(key)
        elif key_type == "phone":
            key = self._normalize_phone(key)
        elif key_type == "cnpj_cpf":
            key = self._normalize_cnpj_cpf(key)
        elif key_type == "evp":
            key = self._normalize_evp(key)
        vals["key"] = key
