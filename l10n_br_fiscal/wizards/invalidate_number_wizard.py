# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class InvalidateNumberWizard(models.TransientModel):
    _name = "l10n_br_fiscal.invalidate.number.wizard"
    _description = "Invalidate Number Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    def do_invalidate(self):
        invalidate = self.env["l10n_br_fiscal.invalidate.number"].create(
            {
                "company_id": self.document_id.company_id.id,
                "document_type_id": self.document_id.document_type_id.id,
                "document_serie_id": self.document_id.document_serie_id.id,
                "number_start": self.document_id.document_number,
                "number_end": self.document_id.document_number,
                "justification": self.justification,
            }
        )
        invalidate._invalidate(self.document_id)

    def doit(self):
        for wizard in self:
            wizard.do_invalidate()
        self._close()
