# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentCorrectionWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.correction.wizard"
    _description = "Fiscal Document Correction Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    justification = fields.Text(
        required=True,
        help="Between 15 and 1000 characters. Line breaks, tabs, repeated "
        "spaces and typographic punctuation are normalized before sending.",
    )

    def doit(self):
        action = None
        for wizard in self:
            if wizard.document_id:
                # Validates before anything is sent to the tax authority
                text = wizard.document_id._normalize_correction_text(
                    wizard.justification
                )
                action = wizard.document_id._document_correction(text) or action
        return action or self._close()
