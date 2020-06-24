# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


from ..constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    PROCESSADOR_NENHUM
)

import logging

_logger = logging.getLogger(__name__)


def filter_processador(record):
    if record.document_electronic and \
            record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class DocumentEletronic(models.AbstractModel):
    _name = "l10n_br_fiscal.document.electronic"
    _description = "Fiscal Eletronic Document"

    _inherit = "l10n_br_fiscal.document.workflow"

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
        copy=False,)

    motivo_situacao = fields.Char(
        string='Motivo situação',
        copy=False,)

    codigo_motivo_situacao = fields.Char(
        compute='_compute_codigo_motivo_situacao',
        string='Situação',
        copy=False,)

    # Eventos de envio
    data_hora_autorizacao = fields.Datetime(
        string="Data Hora",
        readonly=True,
        copy=False)

    protocolo_autorizacao = fields.Char(
        string="Protocolo",
        readonly=True,
        copy=False)

    autorizacao_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.event",
        string="Autorização",
        readonly=True,
        copy=False)

    file_xml_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_sent_id",
        string="XML envio",
        ondelete="restrict",
        copy=False,
        readonly=True)

    file_xml_autorizacao_id = fields.Many2one(
        comodel_name="ir.attachment",
        related="autorizacao_event_id.xml_returned_id",
        string="XML de autorização",
        ondelete="restrict",
        copy=False,
        readonly=True)

    file_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="PDF",
        ondelete="restrict",
        copy=False)

    # Eventos de cancelamento
    data_hora_cancelamento = fields.Datetime(
        string="Data Hora Autorização",
        readonly=True)

    protocolo_cancelamento = fields.Char(
        string="Protocolo Autorização",
        readonly=True)

    cancel_document_event_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.cancel", string="Cancelamento"
    )

    file_xml_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de cancelamento",
        ondelete="restrict",
        copy=False)

    file_xml_autorizacao_cancelamento_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML de autorização de cancelamento",
        ondelete="restrict",
        copy=False)

    document_version = fields.Char(
        string='Versão',
        default='4.00',
        readonly=True)

    is_edoc_printed = fields.Boolean(
        string="Impresso",
        readonly=True)

    def _eletronic_document_send(self):
        """ Implement this method in your transmission module,
        to send the electronic document and use the method _change_state
        to update the state of the transmited document,

        def _eletronic_document_send(self):
            super(DocumentEletronic, self)._document_send()
            for record in self.filtered(myfilter):
                Do your transmission stuff
                [...]
                Change the state of the document
        """
        for record in self.filtered(filter_processador):
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

    def _document_send(self):
        no_electronic = self.filtered(lambda d: not d.document_electronic)
        super(DocumentEletronic, no_electronic)._document_send()

        electronic = self - no_electronic
        electronic._eletronic_document_send()

    def _gerar_evento(self, arquivo_xml, event_type):
        event_obj = self.env["l10n_br_fiscal.document.event"]

        vals = {
            "type": event_type,
            "company_id": self.company_id.id,
            "origin": self.document_type_id.code + "/" + self.number,
            "create_date": fields.Datetime.now(),
            "fiscal_document_id": self.id,
        }
        event_id = event_obj.create(vals)
        event_id._grava_anexo(arquivo_xml, "xml")
        return event_id

    def _exec_after_SITUACAO_EDOC_A_ENVIAR(self, old_state, new_state):
        super(DocumentEletronic, self)._exec_before_SITUACAO_EDOC_A_ENVIAR(
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

    def view_xml(self):
        xml_file = self.file_xml_autorizacao_id or self.file_xml_id
        if not xml_file:
            self._document_export()
            xml_file = self.file_xml_autorizacao_id or self.file_xml_id
        return self._target_new_tab(xml_file)

    def view_pdf(self):
        return self._target_new_tab(self.file_pdf_id)
