# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RtcTreatment(models.Model):
    """Tax treatment of the Reforma Tributaria do Consumo.

    One record per treatment of the official Calculadora de Tributos
    (TRATAMENTO_TRIBUTARIO).  The formulas are not hardcoded: they are the
    official expressions, evaluated by ``l10n_br_fiscal.rtc.engine``, so an
    upstream change only touches this table.
    """

    _name = "l10n_br_fiscal.rtc.treatment"
    _description = "RTC tax treatment"
    _order = "code"

    code = fields.Integer(required=True, index=True)
    name = fields.Char(required=True)

    expr_rate = fields.Char(string="Rate expression")
    expr_effective_rate = fields.Char(string="Effective rate expression")
    expr_base = fields.Char(string="Base expression")
    expr_tax_computed = fields.Char(string="Computed tax expression")
    expr_tax_due = fields.Char(string="Tax due expression")
    expr_deferral_percent = fields.Char(string="Deferral percentage expression")
    expr_deferral_value = fields.Char(string="Deferral value expression")

    has_rate_reduction = fields.Boolean()
    has_reducer = fields.Boolean()
    has_monophase = fields.Boolean()
    has_adjustment = fields.Boolean()
    incompatible_with_suspension = fields.Boolean()
    requires_desoneration_group = fields.Boolean()

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The treatment code must be unique."),
    ]
