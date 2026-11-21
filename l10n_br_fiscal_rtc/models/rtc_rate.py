# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import Decimal

from odoo import api, fields, models


class RtcRate(models.Model):
    """Nominal rate of one RTC tax for a period and a territory.

    The nominal rate is an input of the operation, not a property of the
    cClassTrib: from 2027 on the CBS rate is set by the Senate, and from 2029
    each State and Municipality sets its own IBS rate.  Keeping it in its own
    table avoids multiplying tax records (one per cClassTrib x rate x year).
    """

    _name = "l10n_br_fiscal.rtc.rate"
    _description = "RTC nominal rate"
    _order = "tax, date_start"

    tax = fields.Selection(
        selection=[
            ("is", "IS"),
            ("cbs", "CBS"),
            ("ibs_uf", "IBS - State"),
            ("ibs_mun", "IBS - Municipality"),
        ],
        required=True,
        index=True,
    )
    rate = fields.Float(
        string="Rate (%)",
        digits=(16, 4),
        required=True,
        help="Nominal rate in percent, before any reduction.",
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        domain=[("country_id.code", "=", "BR")],
        help="Leave empty for a nationally uniform rate.",
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        help="Leave empty for a state or national rate.",
    )

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    _sql_constraints = [
        (
            "period_check",
            "check(date_end is null or date_end >= date_start)",
            "The end date must be after the start date.",
        ),
    ]

    @api.model
    def get_rate(self, tax, date, state=None, city=None):
        """Return the rate (percent, as Decimal) applying on ``date``.

        The most specific record wins: city, then state, then the nationwide
        reference rate.  Raises when the official table has no rate yet, which
        is the expected behaviour for 2027+ until the Senate/CGIBS publishes
        the values: better a loud error than a silent wrong rate.
        """
        domain = [
            ("tax", "=", tax),
            ("date_start", "<=", date),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", date),
        ]
        records = self.search(domain)
        if state:
            records = records.filtered(
                lambda record: not record.state_id or record.state_id == state
            )
        if city:
            records = records.filtered(
                lambda record: not record.city_id or record.city_id == city
            )
        if not records:
            raise ValueError(
                f"No RTC {tax} rate for {date} in the official rate table "
                "(l10n_br_fiscal.rtc.rate)."
            )

        def specificity(record):
            return (1 if record.city_id else 0) + (1 if record.state_id else 0)

        best = max(records, key=lambda record: (specificity(record), record.date_start))
        return Decimal(str(best.rate or 0.0))
