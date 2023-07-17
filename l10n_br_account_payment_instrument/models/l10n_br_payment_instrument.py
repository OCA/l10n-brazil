# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

BOLETO_BARCODE_LENGTH = 44
BOLETO_DIGITABLE_LINE_LENGTH = 47


class PaymentInstrument(models.Model):
    """
    This model is used to store payment instruments data, such as boleto and pix
    cobrança. A payment instrument can be associated with more than one account
    payable or receivable entry.
    """

    _name = "l10n_br.payment.instrument"
    _description = "Brazilian payment instrument"

    name = fields.Char(
        compute="_compute_name",
    )
    company_id = fields.Many2one(
        comodel_name="res.company", required=True, default=lambda self: self.env.company
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency"
    )

    line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="payment_instrument_id",
        string="Payable/Receivable Entries",
    )
    instrument_type = fields.Selection(
        selection="_get_instrument_type",
        required=True,
    )

    # BOLETO BUSINESS FIELDS

    boleto_barcode_input = fields.Char(help="Boleto barcode or digitable line")
    boleto_barcode_input_normalized = fields.Char(
        compute="_compute_boleto_data",
        help="Boleto barcode or digitable line without non-digit characters",
    )
    boleto_barcode = fields.Char(compute="_compute_boleto_data")
    boleto_digitable_line = fields.Char(
        compute="_compute_digitable_line",
        help="The digitable line is a human-readable representation of the barcode.",
    )
    boleto_due = fields.Date(
        compute="_compute_boleto_due",
    )
    boleto_bank_id = fields.Many2one(
        comodel_name="res.bank",
        compute="_compute_boleto_bank_id",
    )
    boleto_amount = fields.Monetary(
        compute="_compute_boleto_amount",
        currency_field="company_currency_id",
    )

    # BOLETO RAW DATA FIELDS

    boleto_raw_bank = fields.Char(
        compute="_compute_boleto_data",
    )
    boleto_raw_currency = fields.Char(
        compute="_compute_boleto_data",
    )
    boleto_raw_check_digit_barcode = fields.Char(
        compute="_compute_boleto_data",
    )
    boleto_raw_due_factor = fields.Char(
        compute="_compute_boleto_data",
    )
    boleto_raw_amount = fields.Char(
        compute="_compute_boleto_data",
    )
    boleto_raw_free_field = fields.Char(
        compute="_compute_boleto_data",
    )

    # PIX FIELDS

    pix_qrcode_string = fields.Char()
    pix_qrcode_key = fields.Char(
        compute="_compute_pix_data",
    )
    pix_qrcode_txid = fields.Char(
        help="Transaction ID of the PIX payment.",
        compute="_compute_pix_data",
    )

    @api.depends("pix_qrcode_string")
    def _compute_pix_data(self):

        # /!\
        # The logic to decode the standard EMV QR CODE here is very limited
        # It is not guaranteed to work in all cases.
        # The Ideal is to have a complete implementation for this functionality.
        # Something that does the same at https://pix.nascent.com.br/tools/pix-qr-decoder/

        def emv_to_dict(emv):
            emv_dict = {}
            end = False
            to_process = emv
            while not end:
                _id = to_process[0:2]
                size = int(to_process[2:4])
                value = to_process[4 : 4 + size]
                emv_dict[_id] = value
                to_process = to_process[4 + size :]
                if len(to_process) == 0:
                    end = True
            return emv_dict

        for rec in self:
            if not rec.pix_qrcode_string:
                rec.pix_qrcode_key = False
                rec.pix_qrcode_txid = False
                continue

            try:
                emv_dict = emv_to_dict(rec.pix_qrcode_string)
                for key in emv_dict:
                    if key in ["26", "62"]:
                        emv_dict[key] = emv_to_dict(emv_dict[key])
            except Exception:
                raise ValidationError(_("The QR Code of the PIX is invalid."))

            # Get Payment Key (Key or URL)
            if "26" in emv_dict:
                if "01" in emv_dict["26"]:
                    rec.pix_qrcode_key = emv_dict["26"]["01"]
                elif "25" in emv_dict["26"]:
                    rec.pix_qrcode_key = emv_dict["26"]["25"]
                else:
                    rec.pix_qrcode_key = False
            else:
                rec.pix_qrcode_key = False

            # Get TXID
            if "62" in emv_dict:
                if "05" in emv_dict["62"]:
                    rec.pix_qrcode_txid = emv_dict["62"]["05"]
                else:
                    rec.pix_qrcode_txid = False
            else:
                rec.pix_qrcode_txid = False

    @api.model
    def _get_instrument_type(self):
        return [("boleto", _("Boleto")), ("pix_qrcode", _("PIX QR Code"))]

    # BOLETO METHODS

    @api.depends("boleto_raw_amount")
    def _compute_boleto_amount(self):
        for rec in self:
            if not rec.boleto_raw_amount:
                rec.boleto_amount = False
                continue
            rec.boleto_amount = float(rec.boleto_raw_amount) / 100

    @api.depends("boleto_raw_bank")
    def _compute_boleto_bank_id(self):
        for record in self:
            if not record.boleto_raw_bank:
                record.boleto_bank_id = False
                continue
            record.boleto_bank_id = self.env["res.bank"].search(
                [("code_bc", "=", record.boleto_raw_bank)]
            )

    @api.depends("boleto_raw_due_factor")
    def _compute_boleto_due(self):
        for rec in self:
            rec.boleto_due = self.get_due_date(rec.boleto_raw_due_factor)

    @api.depends("boleto_barcode_input")
    def _compute_boleto_data(self):
        for rec in self:

            # If the input code is empty, clear all fields
            if not rec.boleto_barcode_input:
                rec.boleto_raw_bank = False
                rec.boleto_raw_currency = False
                rec.boleto_raw_check_digit_barcode = False
                rec.boleto_raw_due_factor = False
                rec.boleto_raw_amount = False
                rec.boleto_raw_free_field = False
                rec.boleto_barcode = False
                continue

            # Remove all non-digit characters
            rec.boleto_barcode_input_normalized = "".join(
                c for c in rec.boleto_barcode_input if c.isdigit()
            )

            input_len = len(rec.boleto_barcode_input_normalized)

            if input_len == BOLETO_DIGITABLE_LINE_LENGTH:
                rec.boleto_barcode = self.get_barcode(
                    rec.boleto_barcode_input_normalized
                )
            elif input_len == BOLETO_BARCODE_LENGTH:
                rec.boleto_barcode = rec.boleto_barcode_input_normalized
            else:
                raise ValidationError(
                    _("The boleto barcode or digitable line is invalid.")
                )
            rec.boleto_raw_bank = rec.boleto_barcode[0:3]
            rec.boleto_raw_currency = rec.boleto_barcode[3]
            rec.boleto_raw_check_digit_barcode = rec.boleto_barcode[4]
            rec.boleto_raw_due_factor = rec.boleto_barcode[5:9]
            rec.boleto_raw_amount = rec.boleto_barcode[9:19]
            rec.boleto_raw_free_field = rec.boleto_barcode[19:44]

    @api.depends("boleto_barcode")
    def _compute_digitable_line(self):
        for rec in self:
            if not rec.boleto_barcode:
                rec.boleto_digitable_line = False
                continue
            rec.boleto_digitable_line = self.get_digitable_line(rec.boleto_barcode)

    @api.model
    def get_barcode(self, digitable_line):
        """
        Convert a digitable line to a barcode

        The digitable line contains the same information as the barcode,
        but its layout is different and includes some additional verification codes.
        """

        bank = digitable_line[0:3]
        currency = digitable_line[3]
        check_digit = digitable_line[32]
        due_factor = digitable_line[33:37]
        amount = digitable_line[37:47]

        # The free field is extracted from the digitable line in three parts
        free_first_part = digitable_line[4:9]
        free_second_part = digitable_line[10:20]
        free_third_part = digitable_line[21:31]
        free_field = free_first_part + free_second_part + free_third_part

        return f"{bank}{currency}{check_digit}{due_factor}{amount}{free_field}"

    @api.model
    def get_due_date(self, due_factor):
        """
        Convert a due factor to a due date
        """
        if not due_factor:
            return False
        days = int(due_factor)
        due_date = datetime(1997, 10, 7, 0, 0, 0)
        due_date += timedelta(days=days)
        return due_date

    @api.model
    def get_digitable_line(self, barcode):
        """
        Convert a barcode to a digitable line

        The digitable line contains the same information as the barcode,
        but its layout is different and includes some additional verification codes.
        """

        def generate_mod10_field(value):
            total, weight_factor = 0, 2
            for current_digit in reversed(value):
                weighted_digit = int(current_digit) * weight_factor
                total += sum(int(digit) for digit in str(weighted_digit))
                weight_factor = 1 if weight_factor == 2 else 2
            mod10 = total % 10
            check_digit = 0 if mod10 == 0 else 10 - mod10
            return f"{value}{check_digit}"

        bank = barcode[0:3]
        currency = barcode[3]
        check_digit_barcode = barcode[4]
        due_factor = barcode[5:9]
        amount = barcode[9:19]

        field1 = generate_mod10_field(bank + currency + barcode[19:24])
        field2 = generate_mod10_field(barcode[24:34])
        field3 = generate_mod10_field(barcode[34:44])
        field4 = check_digit_barcode
        field5 = due_factor + amount

        digitable_line = (
            f"{field1[0:5]}.{field1[5:11]} "
            f"{field2[0:5]}.{field2[5:11]} "
            f"{field3[0:5]}.{field3[5:11]} "
            f"{field4} {field5}"
        )

        return digitable_line

    @api.constrains("instrument_type", "boleto_barcode_input")
    def _check_boleto_barcode_input(self):
        for rec in self:
            if rec.instrument_type != "boleto":
                continue
            if not rec.boleto_barcode_input:
                raise ValidationError(
                    _("The barcode/digitable line on the Boleto is required.")
                )
            if len(rec.boleto_barcode_input_normalized) not in (
                BOLETO_DIGITABLE_LINE_LENGTH,
                BOLETO_BARCODE_LENGTH,
            ):
                raise ValidationError(
                    _("The barcode/digitable line on the Boleto is invalid.")
                )

    @api.constrains("instrument_type", "pix_qrcode_string")
    def _check_pix_qrcode_string(self):
        for rec in self:
            if rec.instrument_type != "pix_qrcode":
                continue
            if not rec.pix_qrcode_string:
                raise ValidationError(_("The QR Code of the PIX is required."))

    @api.onchange("instrument_type")
    def _onchange_instrument_type(self):
        """
        Clear the fields that are not used by the selected instrument type
        """
        if self.instrument_type == "pix_qrcode":
            self.boleto_barcode_input = False
        elif self.instrument_type == "boleto":
            self.pix_qrcode_string = False

    def _compute_name(self):
        for rec in self:
            rec.name = False
            if rec.instrument_type == "pix_qrcode":
                rec.name = "Pix"
                if rec.pix_qrcode_string:
                    rec.name += f" {rec.pix_qrcode_string[:30]}..."
            elif rec.instrument_type == "boleto":
                rec.name = "Boleto"
                if rec.boleto_barcode_input:
                    rec.name += f" {rec.boleto_barcode[:30]}..."
