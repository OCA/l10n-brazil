# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants.nfse_nacional import NFSE_NACIONAL_CANCEL_MOTIVES


class DocumentCancelWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.cancel.wizard"

    document_type_code = fields.Char(related="document_id.document_type_id.code")
    nfse_nacional_motive = fields.Selection(
        selection=NFSE_NACIONAL_CANCEL_MOTIVES,
        string="Cancellation Reason Code",
        default="1",
    )

    def do_cancel(self):
        return super(
            DocumentCancelWizard,
            self.with_context(nfse_cancel_motive=self.nfse_nacional_motive),
        ).do_cancel()
