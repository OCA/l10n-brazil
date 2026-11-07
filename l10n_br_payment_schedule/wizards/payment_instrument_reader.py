# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from decimal import Decimal

from brbank.instrumento import ler_brcode, normalizar_codigo_barras

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang

EVP = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _code_amount(code):
    """Amount written in a barcode: always on a boleto, on a guia only when
    the value identifier says it is the actual amount (6 or 8)."""
    if code[0] != "8":
        return Decimal(code[9:19]) / 100
    if code[2] in "68":
        return Decimal(code[4:15]) / 100
    return None


def _pix_key_type(key):
    if "@" in key:
        return "email"
    if key.startswith("+"):
        return "phone"
    if EVP.fullmatch(key.lower()):
        return "evp"
    return "cnpj_cpf"


class PaymentInstrumentReader(models.TransientModel):
    _name = "l10n_br_payment_schedule.instrument.reader"
    _description = "Read the Boleto or Pix of a Payment Schedule Item"

    move_line_id = fields.Many2one(
        comodel_name="account.move.line", required=True, readonly=True
    )
    partner_id = fields.Many2one(related="move_line_id.partner_id")
    text = fields.Char(
        string="Code",
        help="Barcode or digitable line of a boleto or guia, or a Pix copy and "
        "paste code.",
    )
    kind = fields.Selection(
        selection=[("barcode", "Boleto or Guia"), ("pix", "Pix")],
        compute="_compute_reading",
    )
    pix_key = fields.Char(string="Pix Key in the Code", compute="_compute_reading")
    pix_receiver = fields.Char(compute="_compute_reading")
    pix_key_id = fields.Many2one(
        comodel_name="res.partner.pix",
        string="Registered Pix Key",
        compute="_compute_reading",
        help="Pix key of the partner that matches the code.",
    )
    message = fields.Text(compute="_compute_reading")
    error = fields.Char(compute="_compute_reading")

    def _read_code(self):
        """Barcode (44 digits) or BR Code of the text; raises ValueError."""
        text = (self.text or "").strip()
        if text.startswith("000201"):
            return "pix", ler_brcode(text)
        return "barcode", normalizar_codigo_barras(text)

    @api.depends("text", "move_line_id")
    def _compute_reading(self):
        for wizard in self:
            wizard.update(
                {
                    "kind": False,
                    "pix_key": False,
                    "pix_receiver": False,
                    "pix_key_id": False,
                    "message": False,
                    "error": False,
                }
            )
            if not wizard.text:
                continue
            try:
                kind, reading = wizard._read_code()
            except ValueError as error:
                wizard.error = str(error)
                continue
            wizard.kind = kind
            amount = None
            if kind == "pix":
                amount = reading.valor
                wizard.pix_key = reading.chave
                wizard.pix_receiver = reading.nome
                if reading.chave:
                    wizard.pix_key_id = wizard.partner_id.pix_key_ids.filtered(
                        lambda pix, key=reading.chave: pix.key.lower() == key.lower()
                    )[:1]
            else:
                amount = _code_amount(reading)
            wizard.message = wizard._get_amount_message(amount)

    def _get_amount_message(self, amount):
        if amount is None:
            return False
        line = self.move_line_id
        currency = line.company_currency_id
        due = abs(line.amount_residual)
        if not float_compare(float(amount), due, precision_rounding=currency.rounding):
            return False
        return _(
            "The amount of the code (%(code)s) differs from the open amount of the "
            "item (%(due)s).",
            code=formatLang(self.env, float(amount), currency_obj=currency),
            due=formatLang(self.env, due, currency_obj=currency),
        )

    def action_register_pix_key(self):
        """Register on the partner the key read from the code; done by the user,
        never automatically."""
        self.ensure_one()
        if self.kind != "pix" or not self.pix_key or self.pix_key_id:
            raise UserError(_("There is no new Pix key to register."))
        self.env["res.partner.pix"].create(
            {
                "partner_id": self.partner_id.id,
                "key_type": _pix_key_type(self.pix_key),
                "key": self.pix_key,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_apply(self):
        self.ensure_one()
        if not self.kind:
            raise UserError(self.error or _("Read a code first."))
        kind, reading = self._read_code()
        if kind == "pix":
            vals = {"payment_pix_copy_paste": reading.payload}
            if self.pix_key_id:
                vals["partner_pix_id"] = self.pix_key_id.id
        else:
            vals = {"payment_barcode": reading}
        self.move_line_id.write(vals)
        return {"type": "ir.actions.act_window_close"}
