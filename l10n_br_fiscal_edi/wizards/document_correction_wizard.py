# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentCorrectionWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.correction.wizard"
    _description = "Fiscal Document Correction Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    def doit(self):
        for wizard in self:
            if wizard.document_id:
                wizard.document_id._document_correction(wizard.justification)
        self._close()
