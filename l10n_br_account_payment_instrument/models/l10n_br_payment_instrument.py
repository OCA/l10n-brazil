# © 2023 ENGENERE LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

from odoo import _, api, fields, models


class PaymentInstrument(models.Model):
    """
    This model is used to store payment instruments data, such as boleto and pix cobrança.
    A payment instrument can be associated with more than one account payable or receivable entry.
    """

    _name = "l10n_br.payment.instrument"
    _description = "Brazilian payment instrument"

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
        requerid=True,
    )

    # BOLETO BUSINESS FIELDS

    # TODO por o campo em um wizard para ser transient.
    boleto_barcode_entry = fields.Char()
    boleto_barcode = fields.Char()
    boleto_digitable_line = fields.Char(
        compute="_compute_boleto_digitable_line",
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
        compute="_compute_boleto_raw_fields",
    )
    boleto_raw_currency = fields.Char(
        compute="_compute_boleto_raw_fields",
    )
    boleto_raw_check_digit_barcode = fields.Char(
        compute="_compute_boleto_raw_fields",
    )
    boleto_raw_due_factor = fields.Char(
        compute="_compute_boleto_raw_fields",
    )
    boleto_raw_amount = fields.Char(
        compute="_compute_boleto_raw_fields",
    )
    boleto_raw_free_field = fields.Char(
        compute="_compute_boleto_raw_fields",
    )

    # PIX FIELDS

    pix_qrcode_value = fields.Char()

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

    @api.depends("boleto_barcode")
    def _compute_boleto_raw_fields(self):
        for rec in self:
            if not rec.boleto_barcode:
                rec.boleto_raw_bank = False
                rec.boleto_raw_currency = False
                rec.boleto_raw_check_digit_barcode = False
                rec.boleto_raw_due_factor = False
                rec.boleto_raw_amount = False
                rec.boleto_raw_free_field = False
                continue
            rec.boleto_raw_bank = rec.boleto_barcode[0:3]
            rec.boleto_raw_currency = rec.boleto_barcode[3]
            rec.boleto_raw_check_digit_barcode = rec.boleto_barcode[4]
            rec.boleto_raw_due_factor = rec.boleto_barcode[5:9]
            rec.boleto_raw_amount = rec.boleto_barcode[9:19]
            rec.boleto_raw_free_field = rec.boleto_barcode[19:24]

    @api.depends("boleto_barcode")
    def _compute_boleto_digitable_line(self):
        for record in self:
            if not record.boleto_barcode:
                record.boleto_digitable_line = False
                continue
            record.boleto_digitable_line = self.get_digitable_line(
                record.boleto_barcode
            )

    @api.model
    def get_due_date(self, due_factor):
        if not due_factor:
            return False
        days = int(due_factor)
        due_date = datetime(1997, 10, 7, 0, 0, 0)
        due_date += timedelta(days=days)
        return due_date

    @api.model
    def get_digitable_line(self, barcode):
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
