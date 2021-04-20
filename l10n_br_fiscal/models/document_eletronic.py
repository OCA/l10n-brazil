# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2019  KMEE INFORMATICA LTDA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


from ..constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    PROCESSADOR_NENHUM
)


def filter_processador(record):
    if record.document_electronic and \
            record.processador_edoc == PROCESSADOR_NENHUM:
        return True
    return False


class DocumentEletronic(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.electronic'
    _description = 'Fiscal Eletronic Document'
    _inherit = 'l10n_br_fiscal.document.workflow'

    status_code = fields.Char(
        string='Status Code',
        copy=False,
    )

    status_name = fields.Char(
        string='Status Name',
        copy=False,
    )

    status_description = fields.Char(
        compute='_compute_status_description',
        string='Status Description',
        copy=False,
    )

    # Authorization Event Related Fields
    authorization_event_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.event',
        string='Authorization Event',
        readonly=True,
        copy=False,
    )

    authorization_date = fields.Datetime(
        string='Authorization Date',
        readonly=True,
        related='authorization_event_id.protocol_date',
    )

    authorization_protocol = fields.Char(
        string='Authorization Protocol',
        related='authorization_event_id.protocol_number',
        readonly=True,
    )

    send_file_id = fields.Many2one(
        comodel_name='ir.attachment',
        related='authorization_event_id.file_request_id',
        string='Send Document File XML',
        ondelete='restrict',
        readonly=True,
    )

    authorization_file_id = fields.Many2one(
        comodel_name='ir.attachment',
        related='authorization_event_id.file_response_id',
        string='Authorization File XML',
        ondelete='restrict',
        readonly=True,
    )

    # Cancel Event Related Fields
    cancel_event_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.event',
        string='Cancel Event',
        copy=False,
    )

    cancel_date = fields.Datetime(
        string='Cancel Date',
        readonly=True,
        related='cancel_event_id.protocol_date',
    )

    cancel_protocol_number = fields.Char(
        string='Cancel Protocol Number',
        related='cancel_event_id.protocol_number',
        readonly=True,
    )

    cancel_file_id = fields.Many2one(
        comodel_name='ir.attachment',
        related='cancel_event_id.file_response_id',
        string='Cancel File XML',
        ondelete='restrict',
        readonly=True,
    )

    document_version = fields.Char(
        string='Version',
        default='4.00',
        readonly=True)

    is_edoc_printed = fields.Boolean(
        string="Is Printed?",
        readonly=True)

    file_report_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Document Report',
        ondelete='restrict',
        readonly=True,
        copy=False,
    )

    @api.depends('status_code', 'status_name')
    def _compute_status_description(self):
        for record in self:
            if record.status_code:
                record.status_description = '{} - {}'.format(
                    record.status_code or '',
                    record.status_name or '',
                )

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
        # Não remova o no_eletronic!!! Pois não é SELF!
        super(DocumentEletronic, no_electronic)._document_send()

        electronic = self - no_electronic
        electronic._eletronic_document_send()

    def _gerar_evento(self, arquivo_xml, event_type):
        event_obj = self.env["l10n_br_fiscal.event"]

        vals = {
            "type": event_type,
            "company_id": self.company_id.id,
            "origin": self.document_type_id.code + "/" + self.number,
            "create_date": fields.Datetime.now(),
            "document_id": self.id,
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
        xml_file = self.authorization_file_id or self.send_file_id
        if not xml_file:
            self._document_export()
            xml_file = self.authorization_file_id or self.send_file_id
        return self._target_new_tab(xml_file)

    def view_pdf(self):
        return self._target_new_tab(self.file_report_id)
