# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import phonenumbers
from email_validator import EmailSyntaxError, validate_email
from erpbrasil.base.fiscal import cnpj_cpf

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
        ("cnpj_cpf", _("CPF or CNPJ")),
        ("phone", _("Phone Number")),
        ("email", _("E-mail")),
        ("evp", _("Random Key")),
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
                email,
                check_deliverability=False,
            )
        except EmailSyntaxError:
            raise ValidationError(_(f"{email.strip()} is an invalid email"))
        normalized_email = result["local"].lower() + "@" + result["domain_i18n"]
        if len(normalized_email) > 77:
            raise ValidationError(
                _(
                    f"The email is too long, "
                    f"a maximum of 77 characters is allowed: \n{email.strip()}"
                )
            )
        return normalized_email

    def _normalize_phone(self, phone):
        try:
            phonenumber = phonenumbers.parse(phone, "BR")
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValidationError(_(f"Unable to parse {phone}: {str(e)}"))
        if not phonenumbers.is_possible_number(phonenumber):
            raise ValidationError(
                _(f"Impossible number {phone}: probably invalid number of digits.")
            )
        if not phonenumbers.is_valid_number(phonenumber):
            raise ValidationError(
                _(f"Invalid number {phone}: probably incorrect prefix.")
            )
        phone = phonenumbers.format_number(
            phonenumber, phonenumbers.PhoneNumberFormat.E164
        )
        return phone

    def _normalize_cnpj_cpf(self, doc_number):
        doc_number = "".join(char for char in doc_number if char.isdigit())
        if not 11 <= len(doc_number) <= 14:
            raise ValidationError(
                _(
                    f"Invalid Document Number {doc_number}: "
                    f"\nThe CPF must have 11 digits and the CNPJ 14 digits."
                )
            )
        is_valid = cnpj_cpf.validar(doc_number)
        if not is_valid:
            raise ValidationError(_(f"Invalid Document Number: {doc_number}"))
        return doc_number

    def _normalize_evp(self, key):
        # EVP: Endereço Virtual de Pagamento (chave aleatória)
        # ex: 123e4567-e12b-12d1-a456-426655440000
        key = "".join(key.split())
        if len(key) != 36:
            raise ValidationError(
                _(f"Invalid Random Key: {key}, cannot be longer than 35 characters")
            )
        blocks = key.split("-")
        if len(blocks) != 5:
            raise ValidationError(
                _(f"Invalid Random Key: {key}, the key must consist of five blocks.")
            )
        for block in blocks:
            try:
                int(block, 16)
            except ValueError:
                raise ValidationError(
                    _(
                        f"Invalid Random Key: {key} \nthe block {block} "
                        f"is not a valid hexadecimal format."
                    )
                )
        return key

    @api.model
    def create(self, vals):
        self.check_vals(vals)
        return super(PartnerPix, self).create(vals)

    def write(self, vals):
        self.check_vals(vals)
        return super(PartnerPix, self).write(vals)

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
