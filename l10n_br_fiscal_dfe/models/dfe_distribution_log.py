# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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

    fiscal_type = fields.Selection(
        selection=[("nfe", "NF-e"), ("cte", "CT-e")],
        readonly=True,
        index=True,
    )

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

    @api.depends("log_type", "create_date")
    def _compute_display_name(self):
        for record in self:
            date_str = (
                record.create_date.strftime("%d/%m/%Y %H:%M")
                if record.create_date
                else ""
            )
            log_label = dict(record._fields["log_type"].selection).get(
                record.log_type, ""
            )
            record.display_name = f"[{log_label}] {date_str}"
