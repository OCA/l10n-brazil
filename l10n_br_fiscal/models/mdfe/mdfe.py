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

SITUACAO_NFE = [
    ("1", "Autorizada"),
    ("2", "Cancelada"),
    ("3", "Denegada"),
]

SITUACAO_MANIFESTACAO = [
         ("pendente", "Pendente"),
         ("ciente", 'Ciente da operação'),
         ("confirmado", 'Confirmada operação'),
         ("desconhecido", "Desconhecimento"),
         ("nao_realizado", 'Não realizado'),
]


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
        selection=[
            ("0", "Entrada"),
            ("1", "Saída")
        ],
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
    def action_baixa_documento(self):
        self.ensure_one()
        documento = self.sped_consulta_dfe_id.baixa_documentos(manifestos=self)

        if len(documento) > 1:
            view_id = self.env.ref(
                "sped_nfe.sped_documento_ajuste_recebimento_tree").id
            view_type = "tree"

        else:
            view_id = self.env.ref(
                "sped_nfe.sped_documento_ajuste_recebimento_form").id
            view_type = "form"

        return {
            "name": "Baixa documentos",
            "view_mode": "form",
            "view_type": view_type,
            "view_id": view_id,
            "res_id": documento.ids,
            "res_model": "sped.documento",
            "type": "ir.actions.act_window",
            "target": "current",
        }

    @api.multi
    def action_salva_xml(self):

        return self.baixa_attachment(
            self.action_baixa_documento()
        )

    @api.multi
    def baixa_attachment(self, attachment=None):

        return {
            "type": "ir.actions.report.xml",
            "report_type": "controller",
            "report_file":
                "/web/content/ir.attachment/" + str(attachment.id) +
                "/datas/" + attachment.display_name + "?download=true",
        }

    @api.multi
    def action_ciencia_emissao(self):
        for record in self:

            record.sped_consulta_dfe_id.validate_document_configuration(
                record.company_id)

            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.company_id,
                record.key,
                "ciencia_operacao"
            )
            if nfe_result["code"] == "135":
                record.state = "ciente"
            elif nfe_result["code"] == "573":
                record.state = "ciente"
            else:
                raise models.ValidationError(
                    nfe_result["code"] + ' - ' + nfe_result["message"])

        return True

    @api.multi
    def action_confirmar_operacacao(self):
        for record in self:
            record.sped_consulta_dfe_id.validate_document_configuration(
                record.company_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.company_id,
                record.key,
                "confirma_operacao")

            if nfe_result["code"] == "135":
                record.state = "confirmado"
            else:
                raise models.ValidationError(_(
                        nfe_result["code"] + ' - ' + nfe_result["message"])
                )

        return True

    @api.multi
    def action_operacao_desconhecida(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_document_configuration(record.company_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.company_id,
                record.key,
                "desconhece_operacao")

            if nfe_result["code"] == "135":
                record.state = "desconhecido"
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"]))

        return True

    @api.multi
    def action_negar_operacao(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_document_configuration(record.company_id)
            nfe_result = record.sped_consulta_dfe_id.send_event(
                record.company_id,
                record.key,
                "nao_realizar_operacao")

            if nfe_result["code"] == "135":
                record.state = "nap_realizado"
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"]))

        return True

    @api.multi
    def action_download_xmls(self):

        if len(self) == 1:
            if self.state == "pendente":
                self.action_ciencia_emissao()

            return self.baixa_attachment(self.action_download_xml())

        attachments = []

        for record in self:
            attachment = record.action_download_xml()
            attachments.append(attachment)

        monta_anexo = self.env["sped.monta.anexo"].create([])

        attachment_id = monta_anexo.monta_anexo_compactado(attachments)

        return self.baixa_attachment(attachment_id)

    @api.multi
    def action_download_xml(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_document_configuration(record.company_id)
            nfe_result = record.sped_consulta_dfe_id.\
                download_nfe(record.company_id, record.key)

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
    def action_importa_xmls(self):
        for record in self:
            record.sped_consulta_dfe_id.baixa_documentos(manifestos=self)

    @api.multi
    def action_importa_xml(self):
        for record in self:
            record.sped_consulta_dfe_id.\
                validate_document_configuration(record.company_id)
            nfe_result = record.sped_consulta_dfe_id.\
                download_nfe(record.company_id, record.key)

            if nfe_result["code"] == "138":
                nfe = objectify.fromstring(nfe_result["nfe"])
                documento = self.env["sped.documento"].new()
                documento.modelo = nfe.NFe.infNFe.ide.mod.text
                dados = documento.le_nfe(xml=nfe_result["nfe"])
                record.document_id = dados
                return {
                    "name": _("Associar Pedido de Compras"),
                    "view_mode": "form",
                    "view_type": "form",
                    "view_id": self.env.ref("sped_nfe.sped_documento_ajuste_recebimento_form").id,
                    "res_id": dados.id,
                    "res_model": "sped.documento",
                    "type": "ir.actions.act_window",
                    "target": "new",
                    "flags": {"form": {"action_buttons": True, "options": {"mode": "edit"}}},
                }
            else:
                raise models.ValidationError(_(
                    nfe_result["code"] + ' - ' + nfe_result["message"])
                )
