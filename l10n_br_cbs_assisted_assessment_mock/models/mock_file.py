# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import uuid

from odoo import api, fields, models

from odoo.addons.l10n_br_assisted_assessment.constants import (
    LINE_CREDIT,
    LINE_DEBIT,
    SERVICE_LINE_TYPE,
    SERVICE_TYPES,
)
from odoo.addons.l10n_br_cbs_assisted_assessment.constants import (
    PAYMENT_SERVICES,
    PAYMENT_TYPE_PCONT,
    PAYMENT_TYPE_RAD,
    SERVICE_WITHHOLDINGS,
)

MOCK_TICKET_PREFIX = "MOCK-"
MOCK_URL_PREFIX = "mock://"
SAMPLE_KEY = "3526" + ("0" * 40)
SAMPLE_AMOUNT = 10.0
SAMPLE_ACQUIRER = "99888777000166"
SAMPLE_SUPPLIER = "55444333000122"


class CbsAssessmentMockFile(models.Model):
    _name = "l10n_br_cbs_assisted_assessment.mock.file"
    _description = "Local file served in place of a CBS assessment response"
    _order = "id desc"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    service = fields.Selection(selection=SERVICE_TYPES, required=True, index=True)
    period_id = fields.Many2one(
        comodel_name="l10n_br_assisted_assessment.period",
        string="Assessment Period",
        index=True,
        ondelete="set null",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("served", "Served")],
        default="draft",
        required=True,
        index=True,
    )
    ticket = fields.Char(index=True, readonly=True, copy=False)
    payload = fields.Text(required=True)

    @api.depends("service", "state", "ticket")
    def _compute_display_name(self):
        services = dict(self._fields["service"]._description_selection(self.env))
        for record in self:
            record.display_name = " ".join(
                part
                for part in (
                    services.get(record.service),
                    record.state,
                    record.ticket,
                )
                if part
            )

    @api.model
    def _open_request(self, company, service):
        """Bind a local file to a new mock ticket and return the opening answer."""
        period = self._period_being_requested(company)
        prepared = self.search(
            [
                ("company_id", "=", company.id),
                ("service", "=", service),
                ("state", "=", "draft"),
                ("period_id", "=", period.id),
            ],
            order="id",
            limit=1,
        )
        if prepared:
            payload = prepared.payload
            mock_file = prepared
        else:
            payload = json.dumps(
                self._build_payload(period, service), ensure_ascii=False, indent=2
            )
            mock_file = self.create(
                {
                    "company_id": company.id,
                    "service": service,
                    "period_id": period.id,
                    "payload": payload,
                }
            )
        ticket = f"{MOCK_TICKET_PREFIX}{uuid.uuid4().hex}"
        mock_file.write({"ticket": ticket, "state": "served", "payload": payload})
        return {"tiqueteSolicitacao": ticket, "tEASegundos": 1}

    @api.model
    def _payload_for_ticket(self, ticket):
        mock_file = self.search([("ticket", "=", ticket)], limit=1)
        return mock_file.payload if mock_file else False

    @api.model
    def _prepare(self, period, services):
        """Store one draft file per service, replacing a draft already waiting."""
        stored = self.browse()
        for service in services:
            payload = json.dumps(
                self._build_payload(period, service), ensure_ascii=False, indent=2
            )
            draft = self.search(
                [
                    ("company_id", "=", period.company_id.id),
                    ("service", "=", service),
                    ("state", "=", "draft"),
                    ("period_id", "=", period.id),
                ],
                limit=1,
            )
            if draft:
                draft.payload = payload
            else:
                draft = self.create(
                    {
                        "company_id": period.company_id.id,
                        "service": service,
                        "period_id": period.id,
                        "payload": payload,
                    }
                )
            stored |= draft
        return stored

    @api.model
    def _period_being_requested(self, company):
        """Return the period of the request that is opening right now.

        ``_transmit`` passes it in the context. A missing value falls back to
        the current month so a call made outside a period still has a file.
        """
        period_id = self.env.context.get("cbs_assessment_mock_period_id")
        period = self.env["l10n_br_assisted_assessment.period"].browse(
            period_id or False
        )
        if period and period.company_id == company:
            return period
        return self._current_period(company)

    @api.model
    def _current_period(self, company):
        today = fields.Date.context_today(self)
        per_apur = f"{today.year:04d}-{today.month:02d}"
        return self.env["l10n_br_assisted_assessment.period"]._get_or_create(
            company, "cbs", per_apur
        )

    @api.model
    def _build_payload(self, period, service):
        if service in PAYMENT_SERVICES:
            return self._payment_payload(period, service)
        return self._assessment_payload(period, service)

    @api.model
    def _assessment_payload(self, period, service):
        line_type = SERVICE_LINE_TYPE[service]
        lines = period._local_document_lines([line_type])
        items = self._items_from_lines(lines, credit=line_type == LINE_CREDIT)
        if not items:
            items = [self._sample_item(period, credit=line_type == LINE_CREDIT)]
        collection = "creditos" if line_type == LINE_CREDIT else "debitos"
        return {"apuracao": [{"pa": self._pa(period), collection: items}]}

    @api.model
    def _payment_payload(self, period, service):
        if service == SERVICE_WITHHOLDINGS:
            lines = period._local_document_lines([LINE_CREDIT])
            payments = [
                self._withholding_payment(period, self._documents_from_lines(lines))
            ]
        else:
            lines = period._local_document_lines([LINE_DEBIT])
            documents = self._documents_from_lines(lines)
            payments = [
                self._rad_payment(period, documents),
                self._pcont_payment(period, documents),
            ]
        return {
            "apuracao": [
                {
                    "dataArrecadacao": fields.Date.to_string(
                        self._collection_date(period)
                    ),
                    "pagamentos": payments,
                }
            ]
        }

    @api.model
    def _collection_date(self, period):
        """Return a collection day inside the assessment month.

        The DARF due date falls in the following month. The collection date
        of the sample file stays in the month being assessed.
        """
        start = period.date_from
        if not start:
            return fields.Date.context_today(self)
        return start.replace(day=15)

    def _withholding_payment(self, period, documents):
        document, amount = self._first_document(documents)
        line = self._composition(period, document, amount, sequence=1)
        partner = document.partner_id if document else self.env["res.partner"]
        line["niFornecedor"] = self._partner_vat(partner, SAMPLE_SUPPLIER)
        return {
            "numeroDARF": self._darf_number(period, "3"),
            "tipo": int(PAYMENT_TYPE_RAD),
            "composicao": [line],
        }

    def _rad_payment(self, period, documents):
        document, amount = self._first_document(documents)
        line = self._composition(period, document, amount, sequence=1)
        line["niContribuinte"] = self._partner_vat(
            period.company_id.partner_id, "00000000000191"
        )
        return {
            "numeroDARF": self._darf_number(period, "1"),
            "tipo": int(PAYMENT_TYPE_RAD),
            "niAdquirente": SAMPLE_ACQUIRER,
            "composicao": [line],
        }

    def _pcont_payment(self, period, documents):
        _document, amount = self._first_document(documents)
        line = self._composition(
            period, self.env["l10n_br_fiscal.document"], amount, sequence=1
        )
        line.pop("chaveDFE", None)
        return {
            "numeroDARF": self._darf_number(period, "2"),
            "tipo": int(PAYMENT_TYPE_PCONT),
            "niContribuinte": self._partner_vat(
                period.company_id.partner_id, "00000000000191"
            ),
            "composicao": [line],
        }

    def _composition(self, period, document, amount, sequence):
        due = period.date_deadline or fields.Date.context_today(self)
        values = {
            "sequencial": sequence,
            "pa": self._pa(period),
            "vencimento": fields.Date.to_string(due),
            "principal": amount,
            "multa": 0,
            "juros": 0,
            "total": amount,
        }
        if document:
            values["chaveDFE"] = document.document_key
        return values

    def _first_document(self, documents):
        if not documents:
            return self.env["l10n_br_fiscal.document"], SAMPLE_AMOUNT
        document = next(iter(documents))
        return document, documents[document] or SAMPLE_AMOUNT

    @api.model
    def _items_from_lines(self, lines, credit):
        items = []
        for document, amount in self._documents_from_lines(lines).items():
            stamp = self._stamp(document.document_date)
            items.append(
                {
                    "origem": 0,
                    "documento": self._document_model(document),
                    "chave": document.document_key,
                    "emissao": stamp,
                    "registro": stamp,
                    "atualizacao": stamp,
                    "cbs": (
                        self._credit_cbs(amount) if credit else self._debit_cbs(amount)
                    ),
                }
            )
        return items

    @api.model
    def _documents_from_lines(self, lines):
        grouped = {}
        for line in lines:
            document = line.document_id
            if not document.document_key:
                continue
            grouped[document] = grouped.get(document, 0.0) + (line.cbs_value or 0.0)
        return grouped

    @api.model
    def _sample_item(self, period, credit):
        """Return one example line dated inside the assessment month.

        An empty period has no fiscal document to copy. The stand-in still
        has to belong to that month, otherwise the file looks like a document
        issued later than the period it is filed in.
        """
        stamp = self._stamp(period._period_utc_bounds()[0])
        return {
            "origem": 0,
            "documento": 55,
            "chave": SAMPLE_KEY,
            "emissao": stamp,
            "registro": stamp,
            "atualizacao": stamp,
            "cbs": (
                self._credit_cbs(SAMPLE_AMOUNT)
                if credit
                else self._debit_cbs(SAMPLE_AMOUNT)
            ),
        }

    @api.model
    def _debit_cbs(self, amount):
        return {
            "apurado": amount,
            "excedente": 0,
            "inexigivel": 0,
            "suspenso": 0,
            "extinto": 0,
            "saldoDevedor": amount,
        }

    @api.model
    def _credit_cbs(self, amount):
        return {
            "apurado": amount,
            "excedentes": 0,
            "apropriacao": {
                "inapropriavel": 0,
                "suspenso": 0,
                "prescrito": 0,
                "aApropriar": 0,
                "apropriado": amount,
                "utilizacao": {
                    "inutilizavel": 0,
                    "utilizado": 0,
                    "restabelecido": 0,
                    "naoUtilizado": {
                        "saldoCredor": amount,
                        "pedidoRessarcimento": 0,
                    },
                },
            },
        }

    @api.model
    def _document_model(self, document):
        code = document.document_type_id.code or ""
        return int(code) if str(code).isdigit() else 55

    @api.model
    def _pa(self, period):
        year, month = period.per_apur.split("-")
        return f"{month}/{year}"

    @api.model
    def _darf_number(self, period, suffix):
        digits = "".join(char for char in period.per_apur if char.isdigit())
        return f"{digits}{suffix}".ljust(17, "0")[:17]

    @api.model
    def _stamp(self, value):
        moment = fields.Datetime.to_datetime(value) or fields.Datetime.now()
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")

    @api.model
    def _partner_vat(self, partner, fallback):
        digits = "".join(char for char in (partner.vat or "") if char.isdigit())
        return digits or fallback
