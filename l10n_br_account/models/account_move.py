# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    SITUACAO_EDOC_AUTORIZADA,
)


class AccountMove(models.Model):
    _inherit = "account.move"

    def post(self, invoice=False):
        result = super().post(invoice)
        if invoice:
            if (
                invoice.document_type_id
                and invoice.document_electronic
                and invoice.issuer == DOCUMENT_ISSUER_COMPANY
                and invoice.state_edoc != SITUACAO_EDOC_AUTORIZADA
            ):
                self.button_cancel()
        return result
