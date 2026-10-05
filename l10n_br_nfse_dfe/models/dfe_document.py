# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.nfse_dfe import NFSE_STATE_LABELS


class L10nBrFiscalDfeDocument(models.Model):
    _inherit = "l10n_br_fiscal_dfe.document"

    fiscal_type = fields.Selection(
        selection_add=[("nfse", "NFS-e")],
        ondelete={"nfse": "cascade"},
    )

    @api.depends("access_key", "vat", "fiscal_type")
    def _compute_partner_id(self):
        super()._compute_partner_id()
        partner_model = self.env["res.partner"]
        for record in self.filtered(lambda rec: rec.fiscal_type == "nfse"):
            digits = re.sub(r"\D", "", record.vat or "")
            record.partner_id = (
                partner_model.search([("cnpj_cpf_stripped", "=", digits)], limit=1)
                if digits
                else False
            )
        return

    @api.depends("access_key", "vat", "fiscal_type", "company_id.vat")
    def _compute_is_own_document(self):
        super()._compute_is_own_document()
        for record in self.filtered(lambda rec: rec.fiscal_type == "nfse"):
            company_digits = re.sub(r"\D", "", record.company_id.vat or "")
            provider_digits = re.sub(r"\D", "", record.vat or "")
            record.is_own_document = bool(
                company_digits and provider_digits and company_digits == provider_digits
            )
        return

    def _get_document_state_label(self):
        self.ensure_one()
        if self.fiscal_type == "nfse":
            return NFSE_STATE_LABELS.get(self.document_state, self.document_state)
        return super()._get_document_state_label()

    def import_document(self):
        if self.fiscal_type != "nfse":
            return super().import_document()
        complete = self._get_complete_dfe()
        if not complete or not complete.attachment_id:
            raise UserError(
                _("You can only import the NFS-e when the DF-e is completed.")
            )
        return {
            "name": _("Import NFS-e XML"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_file": complete.attachment_id.with_context(
                    bin_size=False
                ).datas,
                "default_company_id": self.company_id.id,
                "default_product_id": self.company_id.nfse_import_product_id.id,
            },
        }
