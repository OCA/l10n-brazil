# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    LINE_CREDIT,
    SERVICE_LINE_TYPE,
    TRIBUTE_CBS,
)

from ..constants import POLL_LIMIT, SERVICE_COLLECTION

_logger = logging.getLogger(__name__)


class AssistedAssessmentRequest(models.Model):
    _inherit = "l10n_br_assessment.request"

    def _is_cbs(self):
        self.ensure_one()
        return self.tribute == TRIBUTE_CBS

    def _transmit(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._transmit()
        return_url = self.return_url or self.company_id._cbs_assessment_webhook_url()
        if not (return_url or "").startswith("https://"):
            # The gateway requires HTTPS; warn instead of blocking so that the
            # homologation environment can be exercised from a dev instance.
            _logger.warning(
                "The CBS assessment callback URL %s is not HTTPS", return_url
            )
        payload = self.env["l10n_br_cbs_assessment.client"]._open_request(
            self.company_id, self.service, return_url
        )
        self.response_text = json.dumps(payload, indent=2, ensure_ascii=False)
        if payload.get("codigoErro"):
            # A refusal is business data, not a failure of the call: raising here
            # would roll the transaction back and lose the reason of the refusal
            # along with the request that the gateway already charged.
            self.write(
                {
                    "state": "error",
                    "error_code": payload.get("codigoErro"),
                    "error_message": payload.get("mensagemErro"),
                }
            )
            _logger.warning(
                "The tax administration refused request %s: %s",
                self.id,
                payload.get("codigoErro"),
            )
            return False
        self.write(
            {
                "state": "requested",
                "return_url": return_url,
                "ticket": payload.get("tiqueteSolicitacao"),
                "estimated_seconds": int(payload.get("tEASegundos") or 0),
                "error_code": False,
                "error_message": False,
            }
        )
        return True

    def _fetch_status(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._fetch_status()
        if not self.ticket:
            raise UserError(
                _("Request %s has no ticket to poll the status with.", self.name)
            )
        return self.env["l10n_br_cbs_assessment.client"]._get_status(
            self.company_id, self.ticket
        )

    def _fetch_payload(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._fetch_payload()
        return self.env["l10n_br_cbs_assessment.client"]._download(self.signed_url)

    def _parse_payload(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._parse_payload()
        collection = SERVICE_COLLECTION.get(self.service)
        if not collection:
            raise UserError(
                _("Service %s does not deliver assessment lines.", self.service)
            )
        try:
            data = json.loads(self.payload)
        except ValueError as error:
            raise UserError(
                _("The downloaded file of %s is not valid JSON.", self.name)
            ) from error
        line_type = SERVICE_LINE_TYPE.get(self.service)
        grouped = {}
        for assessment in data.get("apuracao") or []:
            per_apur = self._per_apur_from_pa(assessment.get("pa"))
            if not per_apur:
                _logger.warning(
                    "Skipping assessment group with unexpected period %s in %s",
                    assessment.get("pa"),
                    self.name,
                )
                continue
            for item in assessment.get(collection) or []:
                grouped.setdefault(per_apur, []).append(
                    self._line_vals(item, line_type)
                )
        return grouped

    @api.model
    def _per_apur_from_pa(self, value):
        """Convert the ``mm/aaaa`` period of the file into ``YYYY-MM``."""
        parts = (value or "").split("/")
        if len(parts) != 2:
            return False
        month, year = parts
        if not (month.isdigit() and year.isdigit()):
            return False
        return f"{int(year):04d}-{int(month):02d}"

    @api.model
    def _line_vals(self, item, line_type):
        values = item.get("cbs") or {}
        vals = {
            "document_key": item.get("chave"),
            "origin": item.get("origem") or 0,
            "document_model": item.get("documento") or 0,
            "date_emission": self._parse_datetime(item.get("emissao")),
            "date_registration": self._parse_datetime(item.get("registro")),
            "date_update": self._parse_datetime(item.get("atualizacao")),
            "value": values.get("apurado") or 0.0,
            "value_detail": values,
        }
        if line_type == LINE_CREDIT:
            vals.update(self._credit_values(values))
        else:
            vals.update(self._debit_values(values))
        return vals

    @api.model
    def _debit_values(self, values):
        return {
            "value_excess": values.get("excedente") or 0.0,
            "value_suspended": values.get("suspenso") or 0.0,
            "value_balance": values.get("saldoDevedor") or 0.0,
        }

    @api.model
    def _credit_values(self, values):
        """Flatten the nested appropriation group of the credits file."""
        appropriation = values.get("apropriacao") or {}
        usage = appropriation.get("utilizacao") or {}
        unused = usage.get("naoUtilizado") or {}
        return {
            "value_excess": values.get("excedentes") or 0.0,
            "value_suspended": appropriation.get("suspenso") or 0.0,
            "value_balance": unused.get("saldoCredor") or 0.0,
        }

    @api.model
    def _cron_poll_requests(self):
        """Advance pending requests without waiting for the callback."""
        for request in self.search(
            [("tribute", "=", TRIBUTE_CBS), ("state", "=", "requested")],
            limit=POLL_LIMIT,
        ):
            try:
                request._check_status()
            except Exception:
                _logger.exception(
                    "CBS assessment status poll failed for request %s", request.id
                )
        for request in self.search(
            [("tribute", "=", TRIBUTE_CBS), ("state", "=", "notified")],
            limit=POLL_LIMIT,
        ):
            try:
                request._download()
                request._apply()
            except Exception:
                _logger.exception(
                    "CBS assessment download failed for request %s", request.id
                )
        return True

    @api.model
    def _cron_request_daily(self):
        """Open the daily debit and credit requests of every configured company.

        The endpoints answer with what changed since the previous query, so a
        regular cadence is what keeps the assessment complete.
        """
        companies = self.env["res.company"].search(
            [("cbs_assessment_client_id", "!=", False)]
        )
        today = fields.Date.context_today(self)
        per_apur = f"{today.year:04d}-{today.month:02d}"
        period_model = self.env["l10n_br_assessment.period"]
        for company in companies:
            period = period_model._get_or_create(company, TRIBUTE_CBS, per_apur)
            for service in SERVICE_COLLECTION:
                try:
                    period._create_request(service)
                except UserError as error:
                    _logger.info(
                        "CBS assessment %s request skipped for %s: %s",
                        service,
                        company.display_name,
                        error,
                    )
                except Exception:
                    _logger.exception(
                        "CBS assessment %s request failed for %s",
                        service,
                        company.display_name,
                    )
        return True
