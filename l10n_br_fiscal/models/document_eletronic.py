# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


from ..constants.fiscal import (
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    PROCESSADOR_NENHUM
)

import logging

_logger = logging.getLogger(__name__)


def fiter_processador_edoc_base(record):
    if record.document_electronic and \
        record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class EletronicDocument(models.AbstractModel):
    _name = "l10n_br_fiscal.document.eletronic"
    _inherit = ["mail.thread",
                "mail.activity.mixin",
                "l10n_br_fiscal.document.mixin",
                "l10n_br_fiscal.document.workflow"]

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

    def _document_export(self):
        pass

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self):
        super(EletronicDocument, self)._exec_before_SITUACAO_EDOC_A_ENVIAR()
        self._document_export()
