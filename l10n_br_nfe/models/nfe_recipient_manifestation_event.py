# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import re

from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.nfe.ws.edoc_legacy import MDeAdapter as edoc_mde
from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.mde import (
    SIT_MANIF_CIENTE,
    SIT_MANIF_CONFIRMADO,
    SIT_MANIF_DESCONHECIDO,
    SIT_MANIF_NAO_REALIZADO,
    SITUACAO_MANIFESTACAO,
)


class NfeRecipientManifestationEvent(models.Model):
    _name = "l10n_br_nfe.recipient_manifestation_event"
    _description = "NFe Recipient Manifestation Event"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    document_number = fields.Float(
        string="Document Number",
        index=True,
        digits=(18, 0),
        related="dfe_access_key_id.document_number",
    )

    key = fields.Char(string="Access Key", size=44, related="dfe_access_key_id.key")

    serie = fields.Char(size=3, index=True, related="dfe_access_key_id.serie")

    event_type = fields.Selection(
        string="Manifestation State",
        selection=SITUACAO_MANIFESTACAO,
        index=True,
    )

    event_type_selection = fields.Selection(
        selection=SITUACAO_MANIFESTACAO,
        default="ciente",
        required=True,
    )

    status = fields.Selection(
        selection=[
            ("rascunho", "Rascunho"),
            ("transmitido", "Transmitido"),
        ],
    )

    environment = fields.Selection(related="company_id.dfe_environment")

    dfe_access_key_id = fields.Many2one(
        string="DF-e", comodel_name="l10n_br_fiscal.dfe_access_key"
    )

    mde_document_type = fields.Selection(
        selection=[
            ("mde_nfe", "NFe"),
            ("mde_nfce", "NFCe"),
        ],
        string="MDe Document Type",
    )

    def name_get(self):
        return [(rec.id, f"{rec.key}") for rec in self]

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
        else:
            inf_evento = result.resposta.retEvento[0].infEvento
            if inf_evento.cStat not in valid_codes:
                code = inf_evento.cStat
                message = inf_evento.xMotivo
            else:
                valid = True

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
            result = getattr(processor, method)(self.key, cnpj_partner)
            self.validate_event_response(result, valid_codes)

    def action_send_event(self, operation, valid_codes, new_state):
        for record in self:
            try:
                record._send_event(operation, valid_codes)
                record.event_type = new_state
            except Exception as e:
                raise e

    def action_confirm_selection(self):
        event_mapping = {
            SIT_MANIF_CIENTE[0]: ("ciencia_da_operacao", ["135"], SIT_MANIF_CIENTE[0]),
            SIT_MANIF_CONFIRMADO[0]: (
                "confirmacao_da_operacao",
                ["135"],
                SIT_MANIF_CONFIRMADO[0],
            ),
            SIT_MANIF_DESCONHECIDO[0]: (
                "desconhecimento_da_operacao",
                ["135"],
                SIT_MANIF_DESCONHECIDO[0],
            ),
            SIT_MANIF_NAO_REALIZADO[0]: (
                "operacao_nao_realizada",
                ["135"],
                SIT_MANIF_NAO_REALIZADO[0],
            ),
        }

        for record in self:
            if record.event_type_selection in event_mapping:
                operation, valid_codes, new_state = event_mapping[
                    record.event_type_selection
                ]
                record.action_send_event(operation, valid_codes, new_state)
                record.event_type_selection = False
            else:
                raise ValidationError(
                    _("Select a manifestation type before confirming")
                )
