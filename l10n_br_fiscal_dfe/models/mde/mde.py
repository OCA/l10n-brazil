# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import logging
import re

from erpbrasil.edoc.mde import MDe as edoc_mde
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ...constants.mde import (
    OPERATION_TYPE,
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
    _name = "l10n_br_fiscal.mde"
    _description = "Recipient Manifestation"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    key = fields.Char(string="Access Key", size=44)

    serie = fields.Char(string="Serie", size=3, index=True)

    number = fields.Float(string="Document Number", index=True, digits=(18, 0))

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )

    emitter = fields.Char(string="Emitter", size=60)

    cnpj_cpf = fields.Char(string="CNPJ/CPF", size=18)

    nsu = fields.Char(string="NSU", size=25, select=True)

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        string="Operation Type",
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

    digest_value = fields.Char(string="Digest Value", size=28)

    inclusion_mode = fields.Char(string="Inclusion Mode", size=255)

    authorization_protocol = fields.Char(string="Authorization protocol", size=60)

    cancellation_protocol = fields.Char(string="Cancellation protocol", size=60)

    document_state = fields.Selection(
        string="Document State",
        selection=SITUACAO_NFE,
        select=True,
    )

    state = fields.Selection(
        string="Manifestation State",
        selection=SITUACAO_MANIFESTACAO,
        select=True,
    )

    dfe_id = fields.Many2one(string="DF-e", comodel_name="l10n_br_fiscal.dfe")

    def name_get(self):
        return [
            (
                rec.id,
                "NFº: {} ({}): {}".format(
                    rec.number, rec.cnpj_cpf, rec.company_id.legal_name
                ),
            )
            for rec in self
        ]

    def _get_processor(self):
        session = Session()
        session.verify = False

        return edoc_mde(
            TransmissaoSOAP(self.dfe_id._get_certificate(), session),
            self.company_id.state_id.ibge_code,
            ambiente=self.dfe_id.environment,
        )

    def validate_event_response(self, result, valid_codes):
        valid = False
        if result.retorno.status_code != 200:
            code = result.resposta.status
            message = result.resposta.reason
        elif result.resposta.cStat != "128":
            code = result.resposta.cStat
            message = result.resposta.xMotivo
        else:
            inf_evento = result.resposta.retEvento[0].infEvento
            if inf_evento.cStat not in valid_codes:
                code = inf_evento.cStat
                message = inf_evento.xMotivo
            else:
                valid = True

        if not valid:
            raise ValidationError(_("Invalid Status Code: %s - %s" % (code, message)))

    def send_event(self, method, valid_codes):
        self.dfe_id.validate_document_configuration()

        processor = self._get_processor()
        cnpj_partner = re.sub("[^0-9]", "", self.company_id.cnpj_cpf)

        if hasattr(processor, method):
            result = getattr(processor, method)(self.key, cnpj_partner)
            self.validate_event_response(result, valid_codes)

    def action_send_event(self, operation, valid_codes, new_state):
        """
        Método para enviar o evento da operação escolhida.
        :param operation:   "ciencia_operacao"
                            "confirma_operacao"
                            "desconhece_operacao"
                            "nao_realizar_operacao"
        :param valid_codes: Lista de códigos de retorno válidos para que a
                            operação seja aceita
        :param new_state: Novo estado tomado pela MDF-e caso um código válido
                          seja retornado
        :return: True caso a operação seja concluída com êxito
        """

        for record in self:
            record.send_event(operation, valid_codes)
            record.state = new_state

    def action_ciencia_emissao(self):
        return self.action_send_event(
            "ciencia_da_operacao", ["135", "573"], SIT_MANIF_CIENTE[0]
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

    def action_download_all_xmls(self):
        if len(self) == 1:
            if self.state == SIT_MANIF_PENDENTE[0]:
                self.action_ciencia_emissao()

            return self.download_attachment(self.action_download_xml())

        attachments = []
        for record in self:
            attachments.append(record.action_download_xml())

        built_attachment = self.env["l10n_br_fiscal.attachment"].create([])
        attachment_id = built_attachment.build_compressed_attachment(attachments)
        return self.download_attachment(attachment_id)

    def action_download_xml(self):
        self.ensure_one()

        xml_document = self.dfe_id.download_nfe(self.key)
        file_name = "NFe%s.xml" % self.key
        return self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(xml_document),
                "store_fname": file_name,
                "description": "XML NFe - Download manifesto do destinatário",
                "res_model": "l10n_br_fiscal.mde",
                "res_id": self.id,
            }
        )

    def create_xml_attachment(self, xml):
        file_name = "resumo_nfe-%s.xml" % self.dfe_id.last_nsu
        self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(xml),
                "store_fname": file_name,
                "description": "NFe via Manifesto",
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def download_attachment(self, attachment_id=None):
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/{id}/{nome}?download=true".format(
                id=attachment_id.id, nome=attachment_id.name
            ),
            "target": "self",
        }
