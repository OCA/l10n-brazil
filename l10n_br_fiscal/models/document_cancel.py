# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentCancel(models.Model):
    _name = "l10n_br_fiscal.document.cancel"
    _inherit = "l10n_br_fiscal.event.abstract"
    _description = "Fiscal Document Cancel Record"

    cancel_document_event_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.event",
        inverse_name="cancel_document_event_id",
        string=u"Eventos",
    )

    @api.multi
    def cancel_document(self, event_id):
        for record in self:
            if not record.document_id or not record.justificative:
                continue

            if not record.document_id._document_cancel(record.justificative):
                continue

            event_id.write({
                'state': 'done',
            })
