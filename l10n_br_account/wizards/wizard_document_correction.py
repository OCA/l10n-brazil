# Copyright (C) 2021  Raphaël Valyi - Akretion <raphael.valyi@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentCorrectionWizard(models.TransientModel):
    _inherit = "l10n_br_fiscal.document.correction.wizard"

    def doit(self):
        result = super().doit()
        for wizard in self:
            if wizard.move_id:
                msg = "Carta de correção: {}".format(wizard.justification)
                self.move_id.message_post(body=msg)
        return result
