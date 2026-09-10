# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DfeDistributionLog(models.Model):
    _name = "l10n_br_fiscal_dfe.distribution_log"
    _description = "DF-e Distribution Log"
    _order = "create_date desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        readonly=True,
    )

    log_type = fields.Selection(
        selection=[
            ("success", "Success"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        required=True,
        default="info",
        readonly=True,
    )

    message = fields.Text(required=True, readonly=True)

    request_xml = fields.Text(
        string="SOAP Request",
        readonly=True,
        help="SOAP envelope sent to SEFAZ",
    )

    response_xml = fields.Text(
        string="SOAP Response",
        readonly=True,
        help="SOAP envelope received from SEFAZ",
    )

    def name_get(self):
        result = []
        for rec in self:
            date_str = (
                rec.create_date.strftime("%d/%m/%Y %H:%M") if rec.create_date else ""
            )
            log_label = dict(rec._fields["log_type"].selection).get(rec.log_type, "")
            result.append((rec.id, f"[{log_label}] {date_str}"))
        return result
