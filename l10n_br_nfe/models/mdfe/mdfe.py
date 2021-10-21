# -*- coding: utf-8 -*-
#
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import base64
import logging

from lxml import objectify

from odoo import _, api, models

_logger = logging.getLogger(__name__)

from odoo.addons.l10n_br_fiscal.constants.mdfe import (
    SIT_MANIF_PENDENTE,
    SIT_MANIF_CIENTE,
    SIT_MANIF_CONFIRMADO,
    SIT_MANIF_DESCONHECIDO,
    SIT_MANIF_NAO_REALIZADO
)


class MDFe(models.Model):
    _inherit = "l10n_br_fiscal.mdfe"

    @api.multi
    def action_import_document(self):
        self.ensure_one()
        document_id = self.dfe_id.download_documents(mdfe_ids=self)

        return {
            "name": "Download Documents",
            "view_mode": "form",
            "view_type": 'tree',
            # "view_id": view_id,
            "res_id": document_id.id,
            "res_model": "l10n_br_fiscal.document",
            "type": "ir.actions.act_window",
            "target": "current",
        }

    @api.multi
    def action_salva_xml(self):

        attachment_id = self.action_import_document()
        return self.download_attachment(attachment_id)

    @api.multi
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
            record.dfe_id.validate_document_configuration(record.company_id)

            nfe_result = record.dfe_id.send_event(
                record.company_id,
                record.key,
                operation
            )
            if nfe_result["code"] in valid_codes:
                record.state = new_state
            else:
                raise models.ValidationError('{} - {}'.format(
                    nfe_result["code"], nfe_result["message"]))

        return True

    @api.multi
    def action_ciencia_emissao(self):
        return self.action_send_event(
            'ciencia_operacao',
            ['135', '573'],
            SIT_MANIF_CIENTE[0]
        )

    @api.multi
    def action_confirmar_operacacao(self):
        return self.action_send_event(
            'confirma_operacao',
            ['135'],
            SIT_MANIF_CONFIRMADO[0]
        )

    @api.multi
    def action_operacao_desconhecida(self):
        return self.action_send_event(
            'desconhece_operacao',
            ['135'],
            SIT_MANIF_DESCONHECIDO[0]
        )

    @api.multi
    def action_negar_operacao(self):
        return self.action_send_event(
            'nao_realizar_operacao',
            ['135'],
            SIT_MANIF_NAO_REALIZADO[0]
        )

    @api.multi
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
            attachment = record.action_download_xml()
            attachments.append(attachment)

        built_attachment = self.env["l10n_br_fiscal.attachment"].create([])

        attachment_id = built_attachment. \
            build_compressed_attachment(attachments)

        return self.download_attachment(attachment_id)

    @api.multi
    def action_download_xml(self):
        for record in self:
            record.dfe_id.validate_document_configuration(record.company_id)
            nfe_result = record.dfe_id.download_nfe(
                record.company_id,
                record.key
            )

            if nfe_result["code"] == "138":

                file_name = "NFe%s.xml" % record.key
                return record.env["ir.attachment"].create(
                    {
                        "name": file_name,
                        "datas": base64.b64encode(nfe_result["nfe"]),
                        "datas_fname": file_name,
                        "description":
                            u'XML NFe - Download manifesto do destinatário',
                        "res_model": "l10n_br_fiscal.mdfe",
                        "res_id": record.id
                    })
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"])
                )

    @api.multi
    def action_import_all_xmls(self):
        for record in self:
            record.dfe_id.download_documents(manifestos=self)

    @api.multi
    def action_import_xml(self):
        for record in self:
            record.dfe_id. \
                validate_document_configuration(record.company_id)
            nfe_result = record.dfe_id. \
                download_nfe(record.company_id, record.key)

            if nfe_result["code"] == "138":
                nfe = objectify.fromstring(nfe_result["nfe"])
                documento = self.env["l10n_br_fiscal.document"].new()
                documento.modelo = nfe.NFe.infNFe.ide.mod.text
                dados = documento.le_nfe(xml=nfe_result["nfe"])
                record.document_id = dados
                return {
                    "name": _("Associar Pedido de Compras"),
                    "view_mode": "form",
                    "view_type": "form",
                    "view_id": self.env.ref(
                        "sped_nfe.sped_documento_ajuste_recebimento_form").id,
                    "res_id": dados.id,
                    "res_model": "l10n_br_fiscal.document",
                    "type": "ir.actions.act_window",
                    "target": "new",
                    "flags": {"form": {"action_buttons": True,
                                       "options": {"mode": "edit"}}},
                }
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"])
                )
