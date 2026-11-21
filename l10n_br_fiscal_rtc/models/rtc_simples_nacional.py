# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RtcSnActivity(models.Model):
    """Official Simples Nacional activity (``cAtivSN``) and its annex."""

    _name = "l10n_br_fiscal.rtc.sn.activity"
    _description = "RTC Simples Nacional activity"
    _order = "code"

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    annex = fields.Char()
    annex_with_factor_r = fields.Char()
    label = fields.Char()
    short_label = fields.Char()
    not_taxable = fields.Boolean()

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    @api.model
    def find(self, code, date):
        if not code:
            return self.browse()
        records = self.search(
            [
                ("code", "=", str(code).zfill(2)),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            order="date_start desc",
            limit=1,
        )
        return records


class RtcSnRegime(models.Model):
    """Simples Nacional apuration matrix: what the CRT generates and where."""

    _name = "l10n_br_fiscal.rtc.sn.regime"
    _description = "RTC Simples Nacional regime"
    _order = "crt"

    crt = fields.Selection(
        selection=[
            ("1", "1 - Simples Nacional"),
            ("2", "2 - Simples, excess of sublimite"),
            ("3", "3 - Regime normal, SN option pending"),
        ],
        required=True,
        index=True,
    )
    name = fields.Char()
    generates_ibs = fields.Boolean()
    destination_due = fields.Selection(
        selection=[
            ("DEVIDO", "Due"),
            ("PENDENTE_SUSPENSO", "Pending / suspended"),
            ("ZERO", "Zero"),
        ]
    )
    destination_pending = fields.Selection(
        selection=[
            ("DEVIDO", "Due"),
            ("PENDENTE_SUSPENSO", "Pending / suspended"),
            ("ZERO", "Zero"),
        ]
    )

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    @api.model
    def find(self, crt, date):
        return self.search(
            [
                ("crt", "=", str(crt)),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            order="date_start desc",
            limit=1,
        )


class RtcSnRevenueType(models.Model):
    """Effect of the type of gross revenue (``tpRBSN``) on the calculation."""

    _name = "l10n_br_fiscal.rtc.sn.revenue.type"
    _description = "RTC Simples Nacional revenue type"
    _order = "code"

    code = fields.Integer(required=True, index=True)
    name = fields.Char()
    composes_revenue = fields.Boolean(
        help="The base is part of the gross revenue of the item."
    )
    is_composes_revenue = fields.Boolean(
        help="Whether the Imposto Seletivo is added to the gross revenue."
    )
    revenue_factor = fields.Float(
        digits=(16, 4),
        help="Fraction of the gross revenue actually taxed (1, 0.5 or 0).",
    )
    pending = fields.Boolean(help="The value is pending/suspended (indirect export).")
    requires_rate = fields.Boolean()
    forbids_not_taxable = fields.Boolean()

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    @api.model
    def find(self, code, date):
        return self.search(
            [
                ("code", "=", int(code)),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            order="date_start desc",
            limit=1,
        )


class RtcSnTransition(models.Model):
    """CBS to IBS shift factor on public purchases, per period."""

    _name = "l10n_br_fiscal.rtc.sn.transition"
    _description = "RTC Simples Nacional transition factor"
    _order = "date_start"

    factor = fields.Float(digits=(16, 4), required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date()

    @api.model
    def find(self, date):
        return self.search(
            [
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            order="date_start desc",
            limit=1,
        )
