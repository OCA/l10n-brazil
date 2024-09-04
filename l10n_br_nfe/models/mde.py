# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import logging
import re

from erpbrasil.transmissao import TransmissaoSOAP
from nfelib.nfe.ws.edoc_legacy import MDeAdapter as edoc_mde
from requests import Session

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.mde import (
    OPERATION_TYPE,
    SCHEMAS,
    SIT_MANIF_CIENTE,
    SIT_MANIF_CONFIRMADO,
    SIT_MANIF_DESCONHECIDO,
    SIT_MANIF_NAO_REALIZADO,
    SIT_MANIF_PENDENTE,
    SITUACAO_MANIFESTACAO,
    SITUACAO_NFE,
)

_logger = logging.getLogger(__name__)


class MDe(models.Model):
    _name = "l10n_br_nfe.mde"
    _description = "Recipient Manifestation"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    key = fields.Char(string="Access Key", size=44)

    serie = fields.Char(size=3, index=True)

    number = fields.Float(string="Document Number", index=True, digits=(18, 0))

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )

    emitter = fields.Char(size=60)

    cnpj_cpf = fields.Char(string="CNPJ/CPF", size=18)

    nsu = fields.Char(string="NSU", size=25, index=True)

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
    )

    document_value = fields.Float(
        string="Document Total Value",
        readonly=True,
        digits=(18, 2),
    )

    ie = fields.Char(string="Inscrição estadual", size=18)

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier (partner)",
    )

    emission_datetime = fields.Datetime(
        string="Emission Date",
        index=True,
        default=fields.Datetime.now,
    )

    inclusion_datetime = fields.Datetime(
        string="Inclusion Date",
        index=True,
        default=fields.Datetime.now,
    )

    authorization_datetime = fields.Datetime(string="Authorization Date", index=True)

    cancellation_datetime = fields.Datetime(string="Cancellation Date", index=True)

    digest_value = fields.Char(size=28)

    inclusion_mode = fields.Char(size=255)

    authorization_protocol = fields.Char(size=60)

    cancellation_protocol = fields.Char(size=60)

    document_state = fields.Selection(
        selection=SITUACAO_NFE,
        index=True,
    )

    state = fields.Selection(
        string="Manifestation State",
        selection=SITUACAO_MANIFESTACAO,
        index=True,
    )

    dfe_id = fields.Many2one(string="DF-e", comodel_name="l10n_br_fiscal.dfe")

    schema = fields.Selection(selection=SCHEMAS)

    attachment_id = fields.Many2one(comodel_name="ir.attachment")

    def name_get(self):
        return [
            (
                rec.id,
                f"NFº: {rec.number} ({rec.cnpj_cpf}): {rec.company_id.legal_name}",
            )
            for rec in self
        ]

    def _get_processor(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False

        return edoc_mde(
            TransmissaoSOAP(certificado, session),
            self.company_id.state_id.ibge_code,
            ambiente=self.dfe_id.environment,
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

    def import_document(self):
        self.ensure_one()

        if self.state == "pendente":
            self.action_ciencia_emissao()

        try:
            document = self.dfe_id._download_document(self.key)
            document_id = self.dfe_id._parse_xml_document(document)
        except Exception as e:
            self.dfe_id.message_post(
                body=_("Error importing document: \n\n %(error)s", error=e)
            )
            return

        if document_id:
            document_id.dfe_id = self.dfe_id.id
            self.document_id = document_id

    def import_document_multi(self):
        for rec in self.filtered(
            lambda m: m.state in (SIT_MANIF_PENDENTE[0], SIT_MANIF_CIENTE[0])
        ):
            rec.import_document()

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
                record.state = new_state
            except Exception as e:
                raise e

    def action_ciencia_emissao(self):
        return self.action_send_event(
            "ciencia_da_operacao", ["135"], SIT_MANIF_CIENTE[0]
        )

    def action_confirmar_operacacao(self):
        return self.action_send_event(
            "confirmacao_da_operacao", ["135"], SIT_MANIF_CONFIRMADO[0]
        )

    def action_operacao_desconhecida(self):
        return self.action_send_event(
            "desconhecimento_da_operacao", ["135"], SIT_MANIF_DESCONHECIDO[0]
        )

    def action_negar_operacao(self):
        return self.action_send_event(
            "operacao_nao_realizada", ["135"], SIT_MANIF_NAO_REALIZADO[0]
        )

    def create_xml_attachment(self, xml):
        file_name = "NFe%s.xml" % self.dfe_id.last_nsu
        self.attachment_id = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(xml),
                "store_fname": file_name,
                "description": "NFe via Manifesto",
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def action_download_xml(self):
        for record in self.filtered(lambda m: m.state == SIT_MANIF_PENDENTE[0]):
            record.action_ciencia_emissao()

        if len(self) == 1:
            return self.download_attachment(self.attachment_id)

        compressed_attachment_id = (
            self.env["l10n_br_fiscal.attachment"]
            .create([])
            .build_compressed_attachment(self.mapped("attachment_id"))
        )
        return self.download_attachment(compressed_attachment_id)

    def download_attachment(self, attachment_id):
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{attachment_id.id}"
                f"/{attachment_id.name}?download=true"
            ),
            "target": "self",
        }
