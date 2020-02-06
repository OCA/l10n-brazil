# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.exceptions import Warning as UserError

from ..constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    PROCESSADOR_NENHUM
)

import logging

_logger = logging.getLogger(__name__)


def fiter_processador_edoc_base(record):
    if record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class EletronicDocument(models.AbstractModel):
    _name = "l10n_br_fiscal.document.eletronic"
    _description = "Fiscal Document"

    # Eventos de envio

    autorizacao_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document_event",
        string="Autorização",
        readonly=True,
        copy=False,
    )
    file_xml_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_sent_id",
        string="XML",
        ondelete="restrict",
        copy=False,
        readonly=True,
    )
    file_xml_autorizacao_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_returned_id",
        string="XML de autorização",
        ondelete="restrict",
        copy=False,
        readonly=True,
    )

    # Eventos de cancelamento

    cancel_document_event_id = fields.Many2one(
        comodel_name="l10n_br_account.invoice.cancel", string="Cancelamento"
    )

    file_xml_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de cancelamento",
        ondelete="restrict",
        copy=False,
    )
    file_xml_autorizacao_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de autorização de cancelamento",
        ondelete="restrict",
        copy=False,
    )
    file_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="PDF DANFE/DANFCE",
        ondelete="restrict",
        copy=False,
    )

    def action_invoice_open(self):
        """ Estamos quebrando a cadei de chamadas pois este método não deve
         ser chamado manualmente no Brasil. Caso você instale algum módulo
         que esteja chamando ele fique atento.
        :return:
        """
        _logger.warning('ALGUM MODULO ESTA CHAMANDO O action_invoice_open')
        return self.action_edoc_confirm()

    def action_invoice_cancel(self):
        """ Estamos quebrando a cadei de chamadas pois este método não deve
         ser chamado manualmente no Brasil. Caso você instale algum módulo
         que esteja chamando ele fique atento.
        :return:
        """
        _logger.warning('ALGUM MODULO ESTA CHAMANDO O action_invoice_cancel')
        return self.action_edoc_cancel()

    def _gerar_evento(self, arquivo_xml, type):
        event_obj = self.env["l10n_br_fiscal.document_event"]

        vals = {
            "type": type,
            "company_id": self.company_id.id,
            "origin": self.document_type_id.code + "/" + self.number,
            "create_date": fields.Datetime.now(),
            "fiscal_document_event_id": self.id,
        }
        event_id = event_obj.create(vals)
        event_id._grava_anexo(arquivo_xml, "xml")
        return event_id

    def _edoc_export(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_A_ENVIAR)

    def _edoc_send(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _edoc_cancel(self):
        for record in self.filtered(fiter_processador_edoc_base):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def edoc_export(self):
        self._edoc_export()

    @api.multi
    def edoc_check(self):
        return True

    def action_number(self):
        for record in self:
            if not record.number:
                record.number = record._create_serie_number(
                    record.document_serie_id.id, record.date
                )
            if not record.key:
                record.gera_nova_chave()

    def action_edoc_confirm(self):
        to_confirm = self.filtered(
            lambda inv: inv.state_edoc != SITUACAO_EDOC_A_ENVIAR
        )

        to_confirm.action_number()
        to_confirm.edoc_check()
        return to_confirm.edoc_export()

    # TODO: Move to account.invoice
    # def action_edoc_send(self):
    #     to_confirm = self.filtered(
    #         lambda inv: inv.state_edoc in (SITUACAO_EDOC_EM_DIGITACAO,
    #                                        SITUACAO_EDOC_REJEITADA))
    #     to_confirm.action_edoc_confirm()
    #     to_send = self.filtered(
    #         lambda inv: inv.state_edoc == SITUACAO_EDOC_A_ENVIAR
    #     )
    #     return to_send._edoc_send()
    #
    # @api.multi
    # def action_invoice_draft(self):
    #     for record in self.filtered(fiter_processador_edoc_base):
    #         record._change_state(SITUACAO_EDOC_EM_DIGITACAO)
    #     return super(EletronicDocument, self).action_invoice_draft()

    @api.multi
    def action_edoc_cancel(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.edoc_protocol_number
        emitente = self.issuer

        if (
            (document_serie_id and fiscal_document_id and not electronic)
            or not nfe_protocol
        ) or emitente == u"1":
            return self._edoc_cancel()
        else:
            result = self.env["ir.actions.act_window"].for_xml_id(
                "edoc_base", "edoc_cancel_wizard_act_window"
            )
            return result

    @api.multi
    def action_edoc_cce(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.edoc_protocol_number
        emitente = self.issuer

        if (
            (document_serie_id and fiscal_document_id and not electronic)
            or not nfe_protocol
        ) or emitente == u"1":
            raise UserError(
                _(
                    "Impossível enviar uma cartão de correção !!!\n"
                    "Para uma nota fiscal não emitida / não eletônica"
                )
            )
        else:
            result = self.env["ir.actions.act_window"].for_xml_id(
                "edoc_base", "edoc_cce_wizard_act_window"
            )
            return result

    @api.multi
    def cancel_invoice_online(self, justificative):
        pass

    @api.multi
    def cce_invoice_online(self, justificative):
        pass

    def serialize(self):
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        return edocs
