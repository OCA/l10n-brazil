# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    DOCUMENT_ISSUER_COMPANY,
)


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        result = super().post(invoice)
        if invoice:
            if (invoice.fiscal_document_id != dummy_doc
                    and invoice.document_electronic
                    and invoice.issuer == DOCUMENT_ISSUER_COMPANY
                    and invoice.state_edoc != SITUACAO_EDOC_AUTORIZADA):
                self.button_cancel()
        return result
