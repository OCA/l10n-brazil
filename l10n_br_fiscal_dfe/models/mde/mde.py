# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from __future__ import division, print_function, unicode_literals

import base64
import logging

from lxml import objectify

from odoo import _, fields, models

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

    def cria_wizard_gerenciamento(self, state=""):
        return self.env["wizard.confirma.acao"].create(
            {
                "manifestacao_ids": [(6, 0, self.ids)],
                "state": state,
            }
        )

    def action_import_document(self):
        self.ensure_one()

        return {
            "name": "Download Documents",
            "view_mode": "form",
            "view_type": "tree",
            "res_id": self.dfe_id.download_documents(mde_ids=self).id,
            "res_model": "l10n_br_fiscal.document",
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def action_salva_xml(self):
        return self.download_attachment(self.action_import_document())

    def download_attachment(self, attachment_id=None):
        return {
            "name": _("Download Attachment"),
            "view_mode": "form",
            "res_model": "ir.attachment",
            "type": "ir.actions.act_window",
            "target": "new",
            "flags": {"mode": "readonly"},
            "res_id": attachment_id.id,
        }

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
            nfe_result = record.dfe_id.send_event(record.key, operation)
            if nfe_result["code"] not in valid_codes:
                raise models.ValidationError(
                    _("{} - {}").format(nfe_result["code"], nfe_result["message"])
                )

            record.state = new_state

    def action_ciencia_emissao(self):
        return self.action_send_event(
            "ciencia_operacao", ["135", "573"], SIT_MANIF_CIENTE[0]
        )

    def action_confirmar_operacacao(self):
        return self.action_send_event(
            "confirma_operacao", ["135"], SIT_MANIF_CONFIRMADO[0]
        )

    def action_operacao_desconhecida(self):
        return self.action_send_event(
            "desconhece_operacao", ["135"], SIT_MANIF_DESCONHECIDO[0]
        )

    def action_negar_operacao(self):
        return self.action_send_event(
            "nao_realizar_operacao", ["135"], SIT_MANIF_NAO_REALIZADO[0]
        )

    def action_download_all_xmls(self):
        if len(self) == 1:
            if self.state == SIT_MANIF_PENDENTE[0]:
                self.action_ciencia_emissao()

            attachment_id = self.action_download_xml()
            # TODO: Message post de Download concluído no formulário do MDF-e
            # TODO: Exibir conversação na MDF-e
            return self.download_attachment(attachment_id)

        attachments = []
        for record in self:
            # TODO: Message post de Download concluído no formulário do MDF-e
            # TODO: Exibir conversação na MDF-e
            attachments.append(record.action_download_xml())

        built_attachment = self.env["l10n_br_fiscal.attachment"].create([])
        attachment_id = built_attachment.build_compressed_attachment(attachments)
        return self.download_attachment(attachment_id)

    def action_download_xml(self):
        self.ensure_one()

        nfe_result = self.dfe_id.download_nfe(self.key)
        if nfe_result["code"] != "138":
            raise models.ValidationError(
                _(nfe_result["code"] + " - " + nfe_result["message"])
            )

        file_name = "NFe%s.xml" % self.key
        return self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(nfe_result["nfe"]),
                "datas_fname": file_name,
                "description": "XML NFe - Download manifesto do destinatário",
                "res_model": "l10n_br_fiscal.mde",
                "res_id": self.id,
            }
        )

    def action_import_all_xmls(self):
        for record in self:
            record.dfe_id.download_documents(mde_ids=self)

    def action_import_xml(self):
        for record in self:
            nfe_result = record.dfe_id.download_nfe(record.key)

            if nfe_result["code"] != "138":
                raise models.ValidationError(
                    _(nfe_result["code"] + " - " + nfe_result["message"])
                )

            nfe = objectify.fromstring(nfe_result["nfe"])
            document_id = self.env["l10n_br_fiscal.document"].new()
            document_id.modelo = nfe.NFe.infNFe.ide.mod.text
            record.document_id = document_id.le_nfe(xml=nfe_result["nfe"])
