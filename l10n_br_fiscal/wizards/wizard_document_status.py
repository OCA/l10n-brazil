# Copyright (C) 2013 Luis Felipe Miléo - KMEE
# Copyright (C) 2014 Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentStatusWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.status.wizard"
    _description = "Fiscal Document Status"

    state = fields.Selection(
        selection=[
            ("init", "Init"),
            ("error", "Error"),
            ("done", "Done")],
        string="State",
        index=True,
        readonly=True,
        default="init")

    document_status = fields.Text(
        string="Status", readonly=True)

    @api.multi
    def get_document_status(self):
        pass
