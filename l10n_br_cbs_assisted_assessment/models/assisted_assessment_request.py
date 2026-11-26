# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_assisted_assessment.constants import (
    LINE_CREDIT,
    SERVICE_LINE_TYPE,
    SERVICE_PAYMENTS,
    SERVICE_WITHHOLDINGS,
    TRIBUTE_CBS,
)

from ..constants import (
    DAILY_SERVICES,
    PAYMENT_SERVICES,
    PAYMENT_TYPE_PCONT,
    PAYMENT_TYPE_RAD,
    POLL_LIMIT,
    SERVICE_COLLECTION,
)

_logger = logging.getLogger(__name__)


class AssistedAssessmentRequest(models.Model):
    _inherit = "l10n_br_assisted_assessment.request"

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
        payload = self.env["l10n_br_cbs_assisted_assessment.client"]._open_request(
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
        return self.env["l10n_br_cbs_assisted_assessment.client"]._get_status(
            self.company_id, self.ticket
        )

    def _fetch_download_link(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._fetch_download_link()
        if not self.ticket:
            raise UserError(
                _(
                    "Request %s has no ticket to fetch the download link with.",
                    self.name,
                )
            )
        return self.env["l10n_br_cbs_assisted_assessment.client"]._get_download_link(
            self.company_id, self.ticket
        )

    def _fetch_payload(self):
        self.ensure_one()
        if not self._is_cbs():
            return super()._fetch_payload()
        return self.env["l10n_br_cbs_assisted_assessment.client"]._download(
            self.signed_url
        )

    def _apply(self):
        self.ensure_one()
        if self._is_cbs() and self.service in PAYMENT_SERVICES:
            return self._apply_payments()
        return super()._apply()

    def _apply_payments(self):
        """Store a DARF file without touching the assessment lines.

        Receiving a payment does not mean the debit and credit of the period
        were downloaded, so the period status stays as it is.
        """
        self.ensure_one()
        if not self.payload:
            raise UserError(_("Request %s has no payload to apply.", self.name))
        period_model = self.env["l10n_br_assisted_assessment.period"]
        payment_model = self.env["l10n_br_cbs_assisted_assessment.payment"]
        periods = period_model.browse()
        for payment_vals in self._parse_payment_payload():
            lines = []
            for line in payment_vals["lines"]:
                period = period_model._get_or_create(
                    self.company_id, self.tribute, line.pop("per_apur")
                )
                periods |= period
                lines.append(dict(line, period_id=period.id))
            payment_vals["lines"] = lines
            payment_model._upsert(self, payment_vals)
        self.write({"state": "done", "period_ids": [fields.Command.set(periods.ids)]})
        if self.period_id and self.period_id not in periods:
            self.period_id._notify_answer_without_data(self, periods)
        return True

    def _delivered_totals(self):
        if self._is_cbs() and self.service in PAYMENT_SERVICES:
            if self.state != "done" or not self.payload:
                return 0, 0.0
            parsed = self._parse_payment_payload()
            lines = [line for payment in parsed for line in payment["lines"]]
            amount = sum(line.get("amount_total") or 0.0 for line in lines)
            return len(lines), amount
        return super()._delivered_totals()

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

    def _parse_payment_payload(self):
        """Convert a recolhimentos or pagamentos file into DARF values."""
        self.ensure_one()
        try:
            data = json.loads(self.payload)
        except ValueError as error:
            raise UserError(
                _("The downloaded file of %s is not valid JSON.", self.name)
            ) from error
        payments = []
        for assessment in data.get("apuracao") or []:
            collection_date = assessment.get("dataArrecadacao")
            for item in assessment.get("pagamentos") or []:
                payment = self._payment_vals(item, collection_date)
                if payment:
                    payments.append(payment)
        return payments

    def _payment_vals(self, item, collection_date):
        payment_type = str(item.get("tipo") or "")
        darf_number = item.get("numeroDARF")
        if payment_type not in (PAYMENT_TYPE_RAD, PAYMENT_TYPE_PCONT) or not (
            darf_number
        ):
            _logger.warning(
                "Skipping payment without a DARF number or type in %s", self.name
            )
            return False
        if self.service == SERVICE_WITHHOLDINGS and payment_type != PAYMENT_TYPE_RAD:
            _logger.warning(
                "Skipping non-RAD payment %s in acquirer withholdings %s",
                darf_number,
                self.name,
            )
            return False
        if not collection_date:
            _logger.warning(
                "Skipping DARF %s without a collection date in %s",
                darf_number,
                self.name,
            )
            return False
        lines = []
        for composition in item.get("composicao") or []:
            line = self._payment_line_vals(composition, payment_type)
            if line:
                lines.append(line)
        return {
            "collection_date": collection_date,
            "darf_number": darf_number,
            "payment_type": payment_type,
            "counterparty_vat": self._payment_counterparty(item, payment_type),
            "lines": lines,
        }

    def _payment_counterparty(self, item, payment_type):
        if self.service != SERVICE_PAYMENTS:
            return False
        if payment_type == PAYMENT_TYPE_RAD:
            return item.get("niAdquirente")
        return item.get("niContribuinte")

    def _payment_line_vals(self, composition, payment_type):
        per_apur = self._per_apur_from_pa(composition.get("pa"))
        if not per_apur:
            _logger.warning(
                "Skipping composition with unexpected period %s in %s",
                composition.get("pa"),
                self.name,
            )
            return False
        sequence = composition.get("sequencial")
        if not sequence:
            _logger.warning("Skipping composition without a sequence in %s", self.name)
            return False
        return {
            "sequence": int(sequence),
            "per_apur": per_apur,
            "date_due": composition.get("vencimento"),
            "counterparty_vat": self._line_counterparty(composition, payment_type),
            "document_key": composition.get("chaveDFE"),
            "amount_principal": composition.get("principal") or 0.0,
            "amount_fine": composition.get("multa") or 0.0,
            "amount_interest": composition.get("juros") or 0.0,
            "amount_total": composition.get("total") or 0.0,
        }

    def _line_counterparty(self, composition, payment_type):
        if self.service == SERVICE_WITHHOLDINGS:
            return composition.get("niFornecedor")
        if payment_type == PAYMENT_TYPE_RAD:
            return composition.get("niContribuinte")
        return False

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
        """Open the daily CBS requests of every configured company.

        The endpoints answer with what changed since the previous query, so a
        regular cadence is what keeps the assessment and the payments complete.
        """
        companies = self.env["res.company"].search(
            [("cbs_assessment_client_id", "!=", False)]
        )
        today = fields.Date.context_today(self)
        per_apur = f"{today.year:04d}-{today.month:02d}"
        period_model = self.env["l10n_br_assisted_assessment.period"]
        for company in companies:
            period = period_model._get_or_create(company, TRIBUTE_CBS, per_apur)
            for service in DAILY_SERVICES:
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
