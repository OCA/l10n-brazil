# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import TP_ATIV, TP_DFE


class DereDeductionLine(models.Model):
    _name = "l10n_br_dere.deduction.line"
    _description = "DeRE deduction line"
    _inherit = "dere.12.infodeducao"
    _order = "dere12_dtEmi, dere12_chDFe"

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
    dere12_tpDFe = fields.Selection(
        TP_DFE,
        string="Fiscal document type",
        help="Official DeRE field tpDFe.",
    )
    dere12_chDFe = fields.Char(
        string="Access key",
        size=53,
        help="Official DeRE field chDFe.",
    )
    dere12_dtEmi = fields.Date(
        string="Issue date",
        required=True,
        help="Official DeRE field dtEmi.",
    )
    dere12_tpAtiv = fields.Selection(
        TP_ATIV,
        string="Activity type",
        required=True,
        help="Official DeRE field tpAtiv.",
    )
    dere12_vOper = fields.Monetary(
        string="Operation amount",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vOper.",
    )
    dere12_vDedTotal = fields.Monetary(
        string="Total deductible",
        currency_field="brl_currency_id",
        help="Official DeRE field vDedTotal. Only in the issue month.",
    )
    dere12_vDed = fields.Monetary(
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

    def _normalized_chdfe(self):
        self.ensure_one()
        return (self.dere12_chDFe or "").replace(" ", "").upper()

    @api.constrains("declaration_id", "dere12_chDFe")
    def _check_unique_chdfe(self):
        for rec in self:
            key = rec._normalized_chdfe()
            if not key:
                continue
            duplicates = rec.declaration_id.deduction_line_ids.filtered(
                lambda line, current=rec, access_key=key: line != current
                and line._normalized_chdfe() == access_key
            )
            if duplicates:
                raise ValidationError(
                    _(
                        "The access key %(key)s cannot be repeated "
                        "in the same assessment period."
                    )
                    % {"key": key}
                )

    @api.constrains("dere12_vDedTotal", "dere12_vOper", "dere12_vDed")
    def _check_deduction_amounts(self):
        for rec in self:
            if rec.dere12_vDedTotal and rec.dere12_vDedTotal - rec.dere12_vOper > 0.005:
                raise ValidationError(
                    _("vDedTotal cannot be greater than vOper for key %s.")
                    % (rec.dere12_chDFe or rec.dere12_dtEmi)
                )
            limit = rec.dere12_vDedTotal if rec.dere12_vDedTotal else rec.dere12_vOper
            if rec.dere12_vDed - limit > 0.005:
                raise ValidationError(
                    _("vDed cannot be greater than the deductible cap for key %s.")
                    % (rec.dere12_chDFe or rec.dere12_dtEmi)
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
        return (
            fields.Date.to_string(self.dere12_dtEmi)[:7] if self.dere12_dtEmi else False
        )

    def _needs_items(self):
        self.ensure_one()
        return (
            self.dere12_tpDFe in ("01", "03", "04")
            and self.dere12_vDedTotal
            and self.dere12_vDedTotal + 0.005 < self.dere12_vOper
        )

    def _to_xml_vals(self):
        self.ensure_one()
        issue_month = self._issue_period() == self.declaration_id.per_apur
        return {
            "tpDFe": self.dere12_tpDFe,
            "chDFe": (self.dere12_chDFe or "").replace(" ", "").upper() or False,
            "dtEmi": fields.Date.to_string(self.dere12_dtEmi),
            "tpAtiv": self.dere12_tpAtiv,
            "vOper": self.dere12_vOper,
            "vDedTotal": (
                self.dere12_vDedTotal
                if issue_month and self.dere12_vDedTotal
                else False
            ),
            "vDed": self.dere12_vDed,
            "items": [item._to_xml_vals() for item in self.item_ids]
            if self._needs_items()
            else [],
        }


class DereDeductionItem(models.Model):
    _name = "l10n_br_dere.deduction.item"
    _description = "DeRE deduction item"
    _inherit = "dere.12.itemdfe"
    _order = "dere12_nItem"

    line_id = fields.Many2one(
        comodel_name="l10n_br_dere.deduction.line",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="line_id.company_id", store=True, index=True)
    dere12_nItem = fields.Char(
        string="Item number",
        required=True,
        size=3,
        help="Official DeRE field nItem.",
    )
    dere12_vItem = fields.Monetary(
        string="Item amount",
        currency_field="brl_currency_id",
        required=True,
        help="Official DeRE field vItem.",
    )
    dere12_vItemDedTotal = fields.Monetary(
        string="Item deductible total",
        currency_field="brl_currency_id",
        help="Official DeRE field vItemDedTotal.",
    )
    dere12_vItemDed = fields.Monetary(
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
            "nItem": self.dere12_nItem,
            "vItem": self.dere12_vItem,
            "vItemDedTotal": self.dere12_vItemDedTotal or False,
            "vItemDed": self.dere12_vItemDed,
        }
