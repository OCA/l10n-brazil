# © 2023 ENGENERE LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PaymentInstrument(models.Model):
    """
    This model is designed to store payment instrument data, including boleto
    and Pix Cobrança.
    A payment instrument may be linked to multiple accounts payable
    or receivable entries.
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
    line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_move_line_payment_instrument_rel",
        column1="payment_instrument_id",
        column2="account_move_line_id",
        string="Payable/Receivable Entries",
    )
    instrument_type = fields.Selection(
        selection="_get_instrument_type",
        required=True,
    )

    # BOLETO BUSINESS FIELDS

    boleto_barcode_input = fields.Char(help="Boleto barcode or digitable line")
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

    # Exemplo de QR Code PIX ESTATICO
    # 00020126540014br.gov.bcb.pix0132pix_marketplace@mercadolibre.com
    # 520400005303986540581.685802BR5906BUBLIM6008Trs Rios62240520mpqr
    # inter5576305139663046792

    # Exemplo de QR Code PIX DINAMICO
    # 00020101021226850014br.gov.bcb.pix2563qrcodepix.bb.com.br/pix/v2/
    # ed3da8bf-115c-47f5-bd03-0edf7f2c5e7b5204000053039865802BR5925SECR
    # ETARIA DA RECEITA FED6008BRASILIA62070503***6304D2D9
    pix_qrcode_string = fields.Char()
    pix_payment_key = fields.Char(
        compute="_compute_pix_data",
    )
    pix_txid = fields.Char(
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
                rec.pix_payment_key = False
                rec.pix_txid = False
                continue
            emv_dict = emv_to_dict(rec.pix_qrcode_string)
            for key in emv_dict:
                if key in ["26", "62"]:
                    emv_dict[key] = emv_to_dict(emv_dict[key])

            # Get Payment Key (Key or URL)
            if "26" in emv_dict:
                if "01" in emv_dict["26"]:
                    rec.pix_payment_key = emv_dict["26"]["01"]
                elif "25" in emv_dict["26"]:
                    rec.pix_payment_key = emv_dict["26"]["25"]
                else:
                    rec.pix_payment_key = False
            else:
                rec.pix_payment_key = False

            # Get TXID
            if "62" in emv_dict:
                if "05" in emv_dict["62"]:
                    rec.pix_txid = emv_dict["62"]["05"]
                else:
                    rec.pix_txid = False
            else:
                rec.pix_txid = False

    @api.model
    def _get_instrument_type(self):
        return [("boleto", _("Boleto")), ("pix", _("PIX Cobrança"))]

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
            input_code = "".join(c for c in rec.boleto_barcode_input if c.isdigit())

            if len(input_code) == 47:
                rec.boleto_barcode = self.get_barcode(input_code)
            elif len(input_code) == 44:
                rec.boleto_barcode = input_code
            else:
                raise UserError(_("The boleto barcode or digitable line is invalid."))
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
            if len(rec.boleto_barcode_input) not in (44, 47):
                raise ValidationError(
                    _("The barcode/digitable line on the Boleto is invalid.")
                )

    @api.constrains("instrument_type", "pix_qrcode_string")
    def _check_pix_qrcode_string(self):
        for rec in self:
            if rec.instrument_type != "pix":
                continue
            if not rec.pix_qrcode_string:
                raise ValidationError(_("The QR Code of the PIX is required."))

    @api.onchange("instrument_type")
    def _onchange_instrument_type(self):
        """
        Clear the fields that are not used by the selected instrument type
        """
        if self.instrument_type == "pix":
            self.boleto_barcode_input = False
        elif self.instrument_type == "boleto":
            self.pix_qrcode_string = False

    def _compute_name(self):
        for rec in self:
            rec.name = False
            if rec.instrument_type == "pix":
                rec.name = "Pix"
                if rec.pix_qrcode_string:
                    rec.name += f" {rec.pix_qrcode_string[:30]}..."
            elif rec.instrument_type == "boleto":
                rec.name = "Boleto"
                if rec.boleto_barcode_input:
                    rec.name += f" {rec.boleto_barcode[:30]}..."
