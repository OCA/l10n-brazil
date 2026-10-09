# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging
import re
from datetime import datetime, timezone

from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.nfe.ws.edoc_legacy import MDeAdapter as edoc_mde
from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import mdest as MD

_logger = logging.getLogger(__name__)


class NfeRecipientManifestationEvent(models.Model):
    _name = "l10n_br_nfe.md_event"
    _description = "Recipient Manifestation"
    _order = "protocol_date DESC, id DESC"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
        required=True,
    )

    document_number = fields.Char()

    access_key = fields.Char(required=True)

    serie = fields.Char()

    event_type = fields.Selection(
        string="Manifestation Type",
        selection=MD.MANIFEST_TYPE,
        default=MD.MANIF_CIENTE,
        index=True,
        required=True,
    )

    event_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.event.type",
        string="Event Type",
        compute="_compute_event_type_id",
        help="SEFAZ event type (tpEvento) of this manifestation, "
        "resolved from the fiscal document event type catalog.",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
    )

    protocol = fields.Char()

    protocol_date = fields.Datetime(string="Registration Date")

    response_xml = fields.Text(string="Response XML")

    environment = fields.Selection(related="company_id.nfe_environment")

    document_type = fields.Selection(
        selection=MD.DOC_TYPE,
        default=MD.NFE,
        required=True,
    )

    def name_get(self):
        return [(rec.id, f"{rec.access_key}") for rec in self]

    @api.depends("event_type")
    def _compute_event_type_id(self):
        codes = {
            MD.MANIF_CIENTE: "210210",
            MD.MANIF_CONFIRMADO: "210200",
            MD.MANIF_DESCONHECIDO: "210220",
            MD.MANIF_NAO_REALIZADO: "210240",
        }
        event_types = self.env["l10n_br_fiscal.event.type"].search(
            [("code", "in", list(set(codes.values())))]
        )
        event_by_code = {event.code: event.id for event in event_types}
        for record in self:
            record.event_type_id = event_by_code.get(
                codes.get(record.event_type), False
            )

    def _get_processor(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False

        return edoc_mde(
            TransmissaoSOAP(certificado, session),
            self.company_id.state_id.ibge_code,
            ambiente=self.environment,
        )

    @api.model
    def validate_event_response(self, result, valid_codes):
        valid = False
        if result.retorno.status_code != 200:
            code = result.retorno.status_code
            message = "Invalid Status Code"
        elif not result.resposta.retEvento:
            # the whole batch was rejected (e.g. schema error): there is no
            # event result, report the batch status instead
            code = result.resposta.cStat
            message = result.resposta.xMotivo
        else:
            inf_evento = result.resposta.retEvento[0].infEvento
            if inf_evento.cStat not in valid_codes:
                if inf_evento.cStat == "573":
                    _logger.warning(
                        "MDE duplicate event (573) for key %s — marking as done",
                        self.access_key,
                    )
                    self.response_xml = result.retorno._content.decode("utf-8")
                    self.state = "done"
                    valid = True
                else:
                    code = inf_evento.cStat
                    message = inf_evento.xMotivo
            else:
                valid = True
                self.protocol = inf_evento.nProt
                self.protocol_date = fields.Datetime.to_string(
                    datetime.fromisoformat(inf_evento.dhRegEvento)
                    .astimezone(timezone.utc)
                    .replace(tzinfo=None)
                )
                self.response_xml = result.retorno._content.decode("utf-8")
                self.state = "done"

        if not valid:
            raise ValidationError(
                _(
                    "Error on validating event: %(code)s - %(msg)s",
                    code=code,
                    msg=message,
                )
            )

    def _send_event(self, method, valid_codes):
        processor = self._get_processor()
        cnpj_partner = re.sub("[^0-9]", "", self.company_id.cnpj_cpf)

        if hasattr(processor, method):
            result = getattr(processor, method)(self.access_key, cnpj_partner)
            self.validate_event_response(result, valid_codes)

    def action_send_event(self, operation, valid_codes, new_state):
        for record in self:
            record._send_event(operation, valid_codes)
            record.event_type = new_state

    def action_confirm(self):
        event_mapping = {
            MD.MANIF_CIENTE: ("ciencia_da_operacao", ["135"]),
            MD.MANIF_CONFIRMADO: ("confirmacao_da_operacao", ["135"]),
            MD.MANIF_DESCONHECIDO: ("desconhecimento_da_operacao", ["135"]),
            MD.MANIF_NAO_REALIZADO: ("operacao_nao_realizada", ["135"]),
        }
        for record in self:
            operation, valid_codes = event_mapping[record.event_type]
            record.action_send_event(operation, valid_codes, record.event_type)
