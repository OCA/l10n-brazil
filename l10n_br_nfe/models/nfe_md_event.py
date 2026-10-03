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
from .document import nfelib_soap_transmission_enabled

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

    justification = fields.Char(
        help="Justification for the 'Operação não Realizada' event "
        "(15-255 characters, required by the SEFAZ)."
    )

    def name_get(self):
        return [(rec.id, f"{rec.access_key}") for rec in self]

    def _get_processor(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False

        return edoc_mde(
            TransmissaoSOAP(certificado, session),
            self.company_id.state_id.ibge_code,
            ambiente=self.environment,
        )

    def _nfelib_get_processor(self):
        """Build the nfelib MdeClient for the MD-e events.

        Drop-in replacement for _get_processor() when the
        l10n_br_nfe.nfelib_soap_transmission parameter is enabled.
        """
        from nfelib.nfe.client.v4_0.mde import MdeClient

        certificate = self.env.company.certificate_nfe_id
        if not certificate:
            raise ValidationError(
                _("Configure an e-CNPJ A1 certificate on the company.")
            )
        import base64

        return MdeClient(
            ambiente=self.environment,
            uf=self.company_id.state_id.ibge_code,
            pkcs12_data=base64.b64decode(certificate.file),
            pkcs12_password=certificate.password,
            wrap_response=True,
        )

    @api.model
    def _retorno_text(self, retorno):
        """Response text from either an erpbrasil requests.Response, a
        brazil-fiscal-client WrappedHTTPResponse or a test double.

        Walk the known payload attributes and keep the first one that really
        is bytes or str: ``content`` is the one exposed by requests and by
        every brazil-fiscal-client release, ``_content`` covers the older
        erpbrasil/test doubles and ``text`` the decoded convenience alias.
        The isinstance checks are required because a MagicMock test double
        answers every attribute access with a truthy mock.
        """
        for attr in ("content", "_content", "text"):
            value = getattr(retorno, attr, None)
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="replace")
            if isinstance(value, str):
                return value
        return ""

    @api.model
    def validate_event_response(self, result, valid_codes):
        valid = False
        if result.retorno.status_code != 200:
            code = result.retorno.status_code
            message = "Invalid Status Code"
        else:
            inf_evento = result.resposta.retEvento[0].infEvento
            if inf_evento.cStat not in valid_codes:
                if inf_evento.cStat == "573":
                    _logger.warning(
                        "MDE duplicate event (573) for key %s — marking as done",
                        self.access_key,
                    )
                    self.response_xml = self._retorno_text(result.retorno)
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
                self.response_xml = self._retorno_text(result.retorno)
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
        use_nfelib = nfelib_soap_transmission_enabled(self.env)
        if use_nfelib:
            processor = self._nfelib_get_processor()
        else:
            processor = self._get_processor()
        cnpj_partner = re.sub("[^0-9]", "", self.company_id.cnpj_cpf)

        if hasattr(processor, method):
            kwargs = {}
            if method == "operacao_nao_realizada" and use_nfelib:
                # the nfelib client requires a 15-255 chars justification
                # (the SEFAZ rejects the 210240 event without one anyway)
                kwargs["justificativa"] = self.justification or _(
                    "Operação não realizada conforme verificado no recebimento."
                )
            result = getattr(processor, method)(self.access_key, cnpj_partner, **kwargs)
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
