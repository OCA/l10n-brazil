# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json

from odoo import api, fields, models

from ..constants import SERPRO_ENDPOINT, SERPRO_SYSTEM, SERVICES


class DctfwebTransmission(models.Model):
    """One call to the Integra Contador, kept for the audit trail.

    A confession sent to the authority has to be reproducible: which service,
    when, what it answered, which receipt came back. The request body is the
    declaration of the company itself, so it is kept; the credentials never
    are, not here and not in the log.
    """

    _name = "l10n_br_dctfweb.transmission"
    _description = "DCTFWeb/MIT Transmission"
    _order = "create_date desc, id desc"

    assessment_id = fields.Many2one(
        comodel_name="l10n_br_dctfweb.assessment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="assessment_id.company_id",
        store=True,
        readonly=True,
    )
    service_key = fields.Char(required=True, readonly=True)
    name = fields.Char(compute="_compute_name", store=True)
    system = fields.Selection(
        selection=SERPRO_SYSTEM,
        readonly=True,
    )
    service = fields.Char(string="Service id", readonly=True)
    endpoint = fields.Selection(
        selection=SERPRO_ENDPOINT,
        readonly=True,
    )
    environment = fields.Char(readonly=True)
    billed = fields.Boolean(
        readonly=True,
        help="The Integra Contador charges for this call.",
    )
    request = fields.Text(
        readonly=True,
        help="The body that was sent, without any credential.",
    )
    response = fields.Text(readonly=True)
    status = fields.Char(readonly=True)
    success = fields.Boolean(readonly=True)
    messages = fields.Text(
        readonly=True,
        help="What the authority answered, code and text.",
    )
    receipt = fields.Char(readonly=True)
    protocol = fields.Char(readonly=True)

    @api.depends("service", "create_date")
    def _compute_name(self):
        for record in self:
            record.name = record.service or record.service_key or "-"

    @api.model
    def log(self, assessment, service_key, request, body):
        """Write the call down. Never called with a header or a token.

        The refusal of the authority is data, not a programming error, so the
        caller reports it back instead of raising: an exception would roll the
        transaction back and take this record with it, losing the trail of
        exactly the call somebody will ask about.
        """
        return self.create(self._log_values(assessment, service_key, request, body))

    @api.model
    def _log_values(self, assessment, service_key, request, body):
        service = SERVICES[service_key]
        transport = self.env["l10n_br_dctfweb.integra.contador"]
        data = (body or {}).get("dados") or {}
        return {
            "assessment_id": assessment.id,
            "service_key": service_key,
            "system": service["system"],
            "service": service["service"],
            "endpoint": service["endpoint"],
            "billed": service["billed"],
            "environment": assessment.company_id.sudo().serpro_environment,
            "request": json.dumps(request, ensure_ascii=False, indent=2),
            "response": json.dumps(body or {}, ensure_ascii=False, indent=2),
            "status": str((body or {}).get("status") or ""),
            "success": transport.succeeded(body or {}),
            "messages": transport.messages(body or {}),
            "protocol": isinstance(data, dict)
            and data.get("protocoloEncerramento")
            or False,
            "receipt": isinstance(data, dict)
            and (data.get("numeroRecibo") or data.get("recibo"))
            or False,
        }
