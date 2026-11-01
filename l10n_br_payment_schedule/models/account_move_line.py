# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from brbank.instrumento import (
    TipoCodigo,
    ler_brcode,
    linha_digitavel_do_codigo,
    normalizar_codigo_barras,
    tipo_codigo,
)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

# CPF, or CNPJ (numeric or alphanumeric), once the punctuation is removed.
DOCUMENT_KEY = re.compile(r"\d{11}|[0-9A-Z]{12}\d{2}")


def _document(value):
    return re.sub(r"[.\-/\s]", "", value or "").upper()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_barcode = fields.Char(
        string="Barcode",
        copy=False,
        help="Barcode (44 digits) of the boleto or guia to pay. The digitable "
        "line is accepted too; the check digits are verified.",
    )
    payment_digitable_line = fields.Char(
        string="Digitable Line",
        compute="_compute_payment_barcode_info",
        store=True,
    )
    payment_barcode_type = fields.Selection(
        selection=[("boleto", "Boleto"), ("guia", "Guia")],
        string="Barcode Type",
        compute="_compute_payment_barcode_info",
        store=True,
    )
    partner_pix_id = fields.Many2one(
        comodel_name="res.partner.pix",
        string="Pix Key",
        copy=False,
        domain="[('partner_id', '=', partner_id)]",
    )
    payment_pix_copy_paste = fields.Char(
        string="Pix Copy and Paste",
        copy=False,
        help="Pix copy and paste code (BR Code) given by the supplier.",
    )
    payment_pix_check = fields.Selection(
        selection=[
            ("checked", "Receiver Checked"),
            ("to_check", "To Check at the Bank"),
            ("mismatch", "Receiver Differs from the Partner"),
        ],
        string="Pix Receiver",
        compute="_compute_payment_pix_check",
        store=True,
        help="Checked: the Pix key is the CNPJ or CPF of the partner. To check at "
        "the bank: other key types and dynamic QR codes, whose receiver only the "
        "bank can confirm.",
    )

    @api.model
    def _normalize_payment_instrument_vals(self, vals):
        if vals.get("payment_barcode"):
            try:
                vals["payment_barcode"] = normalizar_codigo_barras(
                    vals["payment_barcode"]
                )
            except ValueError as error:
                raise ValidationError(
                    _("Invalid barcode or digitable line: %s", error)
                ) from error
        if vals.get("payment_pix_copy_paste"):
            try:
                vals["payment_pix_copy_paste"] = ler_brcode(
                    vals["payment_pix_copy_paste"]
                ).payload
            except ValueError as error:
                raise ValidationError(
                    _("Invalid Pix copy and paste code: %s", error)
                ) from error
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_payment_instrument_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._normalize_payment_instrument_vals(vals)
        return super().write(vals)

    @api.depends("payment_barcode")
    def _compute_payment_barcode_info(self):
        for line in self:
            code = line.payment_barcode
            line.payment_digitable_line = code and linha_digitavel_do_codigo(code)
            line.payment_barcode_type = code and (
                "guia" if tipo_codigo(code) == TipoCodigo.GUIA else "boleto"
            )

    def _get_payment_pix_receiver_key(self):
        """Pix key to check, and whether only the bank can tell the receiver."""
        self.ensure_one()
        if self.payment_pix_copy_paste:
            brcode = ler_brcode(self.payment_pix_copy_paste)
            return brcode.chave, brcode.dinamico
        return self.partner_pix_id.key, False

    @api.depends(
        "payment_pix_copy_paste",
        "partner_pix_id.key",
        "partner_id.commercial_partner_id.vat",
    )
    def _compute_payment_pix_check(self):
        for line in self:
            check = False
            if line.payment_pix_copy_paste or line.partner_pix_id:
                key, dynamic = line._get_payment_pix_receiver_key()
                key = _document(key)
                if dynamic or not DOCUMENT_KEY.fullmatch(key):
                    check = "to_check"
                else:
                    partner = _document(line.partner_id.commercial_partner_id.vat)
                    check = "checked" if key == partner else "mismatch"
            line.payment_pix_check = check

    def _has_payment_transactional_bank_account(self):
        self.ensure_one()
        banks = self.partner_bank_id or self.partner_id.bank_ids
        return any(banks.mapped("transactional_acc_type"))

    @api.depends("payment_barcode", "partner_pix_id", "payment_pix_check")
    def _compute_payment_schedule_state(self):
        return super()._compute_payment_schedule_state()

    def _is_payment_schedule_instrument_missing(self):
        """Boleto needs the barcode; Pix needs a key (or a transactional bank
        account of the partner) and a receiver that is not another person; TED
        and DOC need a bank account of the partner."""
        if super()._is_payment_schedule_instrument_missing():
            return True
        kind = self.payment_mode_id.payment_mode_domain
        if kind == "boleto":
            return not self.payment_barcode
        if kind == "pix_transfer":
            return self.payment_pix_check == "mismatch" or not (
                self.partner_pix_id or self._has_payment_transactional_bank_account()
            )
        if kind in ("ted", "doc"):
            return not (self.partner_bank_id or self.partner_id.bank_ids)
        return False

    @api.model
    def _get_payment_schedule_missing_instrument_domain(self):
        mode_kind = "payment_mode_id.payment_mode_domain"
        typed_banks = self.env["res.partner.bank"].search(
            [("transactional_acc_type", "!=", False)]
        )
        no_transactional_bank = expression.OR(
            [
                [
                    ("partner_bank_id", "!=", False),
                    ("partner_bank_id", "not in", typed_banks.ids),
                ],
                [
                    ("partner_bank_id", "=", False),
                    ("partner_id", "not in", typed_banks.partner_id.ids),
                ],
            ]
        )
        return expression.OR(
            [
                super()._get_payment_schedule_missing_instrument_domain(),
                [(mode_kind, "=", "boleto"), ("payment_barcode", "=", False)],
                [
                    (mode_kind, "=", "pix_transfer"),
                    ("payment_pix_check", "=", "mismatch"),
                ],
                expression.AND(
                    [
                        [
                            (mode_kind, "=", "pix_transfer"),
                            ("partner_pix_id", "=", False),
                        ],
                        no_transactional_bank,
                    ]
                ),
                [
                    (mode_kind, "in", ("ted", "doc")),
                    ("partner_bank_id", "=", False),
                    ("partner_id.bank_ids", "=", False),
                ],
            ]
        )

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if self.payment_barcode:
            vals["barcode"] = self.payment_barcode
            vals["digitable_line"] = self.payment_digitable_line
        if self.partner_pix_id:
            vals["partner_pix_id"] = self.partner_pix_id.id
        return vals

    def action_payment_instrument_reader(self):
        self.ensure_one()
        return {
            "name": _("Read Boleto or Pix"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_payment_schedule.instrument.reader",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_line_id": self.id},
        }
