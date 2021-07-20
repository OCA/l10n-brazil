# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2021  Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentCancelWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.cancel.wizard"

    def do_cancel(self):
        super().do_cancel()
        if self.invoice_id:
            self.invoice_id.action_cancel()
            msg = "Cancelamento: {}".format(self.justification)
            self.invoice_id.message_post(body=msg)
