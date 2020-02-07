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

    @api.depends('codigo_situacao', 'motivo_situacao')
    def _compute_codigo_motivo_situacao(self):
        for record in self:
            if record.motivo_situacao and record.codigo_situacao:
                record.codigo_motivo_situacao = '{} - {}'.format(
                    record.codigo_situacao,
                    record.motivo_situacao
                )

    codigo_situacao = fields.Char(
        string='Código situação',
    )

    motivo_situacao = fields.Char(
        string='Motivo situação',
    )

    codigo_motivo_situacao = fields.Char(
        compute='_compute_codigo_motivo_situacao',
        string='Situação'
    )

    # Eventos de envio
    data_hora_autorizacao = fields.Datetime(
        string="Data Hora",
        readonly=True,
    )
    protocolo_autorizacao = fields.Char(
        string="Protocolo",
        readonly=True,
    )
    autorizacao_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document_event",
        string="Autorização",
        readonly=True,
        copy=False,
    )
    file_xml_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_sent_id",
        string="XML envio",
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
    file_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="PDF",
        ondelete="restrict",
        copy=False,
    )

    # Eventos de cancelamento
    data_hora_cancelamento = fields.Datetime(
        string="Data Hora Autorização",
        readonly=True,
    )
    protocolo_cancelamento = fields.Char(
        string="Protocolo Autorização",
        readonly=True,
    )
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

    document_version = fields.Char(
        string='Versão',
        readonly=True,
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

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        super(EletronicDocument, self)._exec_before_SITUACAO_EDOC_A_ENVIAR(
            old_state, new_state
        )
        self._document_export()

    def serialize(self):
        edocs = []
        self._serialize(edocs)
        return edocs

    def _serialize(self, edocs):
        return edocs

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                'type' : 'ir.actions.act_url',
                'url': '/web/content/{id}/{nome}'.format(
                    id=attachment_id.id,
                    nome=attachment_id.name),
                'target': 'new',
                }

    def visualizar_xml(self):
        xml_file = self.file_xml_autorizacao_id or self.file_xml_id
        return self._target_new_tab(xml_file)

    def visualizar_pdf(self):
        return self._target_new_tab(self.file_pdf_id)
