# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import TP_ATIV


class DereDeductionLine(models.Model):
    _name = "l10n_br_dere.deduction.line"
    _description = "DeRE deduction line"
    _inherit = "spec.mixin.dere.currency"
    _order = "dt_emi, ch_dfe"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="declaration_id.company_id", store=True, index=True
    )
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal document",
        ondelete="restrict",
    )
    tp_dfe = fields.Selection(
        [
            ("01", "DeRE"),
            ("02", "NFS-e"),
            ("03", "NF-e"),
            ("04", "NFC-e"),
            ("05", "NF-e ABI"),
        ],
        string="Fiscal document type",
        help="Official DeRE field tpDFe.",
    )
    ch_dfe = fields.Char(
        string="Access key",
        size=53,
        help="Official DeRE field chDFe.",
    )
    dt_emi = fields.Date(
        string="Issue date",
        required=True,
        help="Official DeRE field dtEmi.",
    )
    tp_ativ = fields.Selection(
        TP_ATIV,
        string="Activity type",
        required=True,
        help="Official DeRE field tpAtiv.",
    )
    v_oper = fields.Monetary(
        string="Operation amount",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vOper.",
    )
    v_ded_total = fields.Monetary(
        string="Total deductible",
        currency_field="brl_currency_id",
        help="Official DeRE field vDedTotal. Only in the issue month.",
    )
    v_ded = fields.Monetary(
        string="Deduction this period",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vDed.",
    )
    item_ids = fields.One2many(
        comodel_name="l10n_br_dere.deduction.item",
        inverse_name="line_id",
        string="Deduction items",
    )

    @api.constrains("v_ded_total", "v_oper", "v_ded")
    def _check_deduction_amounts(self):
        for rec in self:
            if rec.v_ded_total and rec.v_ded_total - rec.v_oper > 0.005:
                raise ValidationError(
                    _("vDedTotal cannot be greater than vOper for key %s.")
                    % (rec.ch_dfe or rec.dt_emi)
                )
            limit = rec.v_ded_total if rec.v_ded_total else rec.v_oper
            if rec.v_ded - limit > 0.005:
                raise ValidationError(
                    _("vDed cannot be greater than the deductible cap for key %s.")
                    % (rec.ch_dfe or rec.dt_emi)
                )

    def write(self, vals):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().unlink()

    def _issue_period(self):
        self.ensure_one()
        return fields.Date.to_string(self.dt_emi)[:7] if self.dt_emi else False

    def _needs_items(self):
        self.ensure_one()
        return (
            self.tp_dfe in ("01", "03", "04")
            and self.v_ded_total
            and self.v_ded_total + 0.005 < self.v_oper
        )

    def _to_xml_vals(self):
        self.ensure_one()
        issue_month = self._issue_period() == self.declaration_id.per_apur
        vals = {
            "tpDFe": self.tp_dfe,
            "chDFe": (self.ch_dfe or "").replace(" ", "").upper() or False,
            "dtEmi": fields.Date.to_string(self.dt_emi),
            "tpAtiv": self.tp_ativ,
            "vOper": self.v_oper,
            "vDedTotal": (
                self.v_ded_total if issue_month and self.v_ded_total else False
            ),
            "vDed": self.v_ded,
            "items": [item._to_xml_vals() for item in self.item_ids]
            if self._needs_items()
            else [],
        }
        return vals


class DereDeductionItem(models.Model):
    _name = "l10n_br_dere.deduction.item"
    _description = "DeRE deduction item"
    _inherit = "spec.mixin.dere.currency"
    _order = "n_item"

    line_id = fields.Many2one(
        comodel_name="l10n_br_dere.deduction.line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="line_id.company_id", store=True, index=True)
    n_item = fields.Char(
        string="Item number",
        required=True,
        size=3,
        help="Official DeRE field nItem.",
    )
    v_item = fields.Monetary(
        string="Item amount",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vItem.",
    )
    v_item_ded_total = fields.Monetary(
        string="Item deductible total",
        currency_field="brl_currency_id",
        help="Official DeRE field vItemDedTotal.",
    )
    v_item_ded = fields.Monetary(
        string="Item deduction this period",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vItemDed.",
    )

    def write(self, vals):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.line_id.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().write(vals)

    def unlink(self):
        if not self.env.context.get(
            "dere_force_declaration_write"
        ) and self.line_id.declaration_id.filtered(lambda rec: rec.state == "closed"):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )
        return super().unlink()

    def _to_xml_vals(self):
        self.ensure_one()
        return {
            "nItem": self.n_item,
            "vItem": self.v_item,
            "vItemDedTotal": self.v_item_ded_total or False,
            "vItemDed": self.v_item_ded,
        }
