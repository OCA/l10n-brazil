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
        help="NF-e: 15 to 1000 characters; line breaks, tabs, repeated spaces and "
        "typographic punctuation are normalized before sending.",
    )

    def doit(self):
        action = None
        for wizard in self:
            if wizard.document_id:
                action = (
                    wizard.document_id._document_correction(wizard.justification)
                    or action
                )
        return action or self._close()
