# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RtcNomenclature(models.Model):
    """NCM/NBS codes accepted by a cClassTrib, per annex of LC 214/2025.

    The official annexes list codes of 4 to 8 digits: a shorter code is a
    prefix that covers every longer code below it.  Matching is therefore done
    on the longest prefix, never on strict equality.
    """

    _name = "l10n_br_fiscal.rtc.nomenclature"
    _description = "RTC nomenclature applicability"
    _order = "classification_code, nomenclature_type, code"

    classification_code = fields.Char(required=True, index=True)
    nomenclature_type = fields.Selection(
        selection=[("ncm", "NCM"), ("nbs", "NBS")],
        required=True,
    )
    code = fields.Char(required=True, index=True)
    annex = fields.Char()

    date_start = fields.Date(required=True)
    date_end = fields.Date()

    @api.model
    def _date_domain(self, date):
        return [
            ("date_start", "<=", date),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", date),
        ]

    @api.model
    def match(self, classification_code, code, nomenclature_type=None, date=None):
        """Return the annex record covering ``code``, or an empty recordset.

        ``code`` is compared as a prefix: an annex line «1006» covers
        «10063021».  The longest matching prefix wins, so the returned record
        is the most specific annex item.
        """
        if not classification_code or not code:
            return self.browse()
        date = date or fields.Date.context_today(self)
        digits = "".join(char for char in str(code) if char.isdigit())
        domain = [("classification_code", "=", classification_code)]
        domain += self._date_domain(date)
        if nomenclature_type:
            domain.append(("nomenclature_type", "=", nomenclature_type))
        candidates = [
            record
            for record in self.search(domain)
            if digits.startswith(record.code or "")
        ]
        if not candidates:
            return self.browse()
        return max(candidates, key=lambda record: len(record.code))

    @api.model
    def is_applicable(
        self, classification_code, code, nomenclature_type=None, date=None
    ):
        return bool(self.match(classification_code, code, nomenclature_type, date))
