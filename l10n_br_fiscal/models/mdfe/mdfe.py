# -*- coding: utf-8 -*-
#
# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import _, api, fields, models
import base64
from lxml import objectify

_logger = logging.getLogger(__name__)

from ...constants.mdfe import (
    SIT_MANIF_PENDENTE,
    SIT_MANIF_CIENTE,
    SIT_MANIF_CONFIRMADO,
    SIT_MANIF_DESCONHECIDO,
    SIT_MANIF_NAO_REALIZADO,
    SIT_NFE_AUTORIZADA,
    SIT_NFE_CANCELADA,
    SIT_NFE_DENEGADA,

    OPERATION_TYPE,
    SITUACAO_MANIFESTACAO,
    SITUACAO_NFE
)


class MDFe(models.Model):
    _name = "l10n_br_fiscal.mdfe"
    _description = 'Recipient Manifestation'

    @api.multi
    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.number, rec.cnpj_cpf, rec.company_id.legal_name)
                 ) for rec in self]

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    key = fields.Char(
        string="Access Key",
        size=44,
    )
    serie = fields.Char(
        string="Serie",
        size=3,
        index=True,
    )
    number = fields.Float(
        string="Document Number",
        index=True,
        digits=(18, 0),
    )
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
    )
    emitter = fields.Char(
        string="Emitter",
        size=60,
    )
    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        size=18,
    )

    nsu = fields.Char(
        string="NSU",
        size=25,
        select=True,
    )

    operation_type = fields.Selection(
        selection=OPERATION_TYPE,
        string="Operation Type",
    )

    document_value = fields.Float(
        string="Document Total Value",
        readonly=True,
        digits=(18, 2),
    )

    ie = fields.Char(
        string="Inscrição estadual",
        size=18,
    )
    # TODO: Verificar qual comodel_name utilizar
    # partner_id = fields.Many2one(
    #     comodel_name="l10n_br_fiscal.partner.profile",
    #     string="Supplier",
    # )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier (partner)",
    )

    supplier = fields.Char(
        string="Supplier",
        size=60,
        index=True,
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
    authorization_datetime = fields.Datetime(
        string="Authorization Date",
        index=True,
    )
    cancellation_datetime = fields.Datetime(
        string="Cancellation Date",
        index=True,
    )
    digest_value = fields.Char(
        string="Digest Value",
        size=28,
    )
    inclusion_mode = fields.Char(
        string="Inclusion Mode",
        size=255,
    )
    authorization_protocol = fields.Char(
        string="Authorization protocol",
        size=60,
    )
    cancellation_protocol = fields.Char(
        string="Cancellation protocol",
        size=60,
    )

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
    dfe_id = fields.Many2one(
        string="DF-e",
        comodel_name="l10n_br_fiscal.dfe",
    )

    @api.multi
    def cria_wizard_gerenciamento(self, state=""):

        dados = {
            "manifestacao_ids": [(6, 0, self.ids)],
            "state": state,
        }

        return self.env["wizard.confirma.acao"].create(dados)

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
    def download_attachment(self, attachment_id=None):

        action = {
            'name': _('Download Attachment'),
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'flags': {'mode': 'readonly'}, # default is 'edit'
            'res_id': attachment_id.id,
        }

        return action

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

            return self.download_attachment(self.action_download_xml())

        attachments = []

        for record in self:
            attachment = record.action_download_xml()
            attachments.append(attachment)

        monta_anexo = self.env["l10n_br_fiscal.attachment"].create([])

        attachment_id = monta_anexo.build_compressed_attachment(attachments)

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
            record.dfe_id.\
                validate_document_configuration(record.company_id)
            nfe_result = record.dfe_id.\
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
                    "view_id": self.env.ref("sped_nfe.sped_documento_ajuste_recebimento_form").id,
                    "res_id": dados.id,
                    "res_model": "l10n_br_fiscal.document",
                    "type": "ir.actions.act_window",
                    "target": "new",
                    "flags": {"form": {"action_buttons": True, "options": {"mode": "edit"}}},
                }
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"])
                )
