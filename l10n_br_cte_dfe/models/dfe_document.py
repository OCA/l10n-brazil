# Copyright 2026 Engenere.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO

from odoo import _, models
from odoo.exceptions import UserError

from ..constants.cte_dfe import CTE_IMPORTABLE_SCHEMAS, SITUACAO_CTE

try:
    from brazilfiscalreport.dacte import Dacte
except ImportError:
    Dacte = None


class L10nBrFiscalDfeDocument(models.Model):
    """CT-e specific features for DF-e documents."""

    _inherit = "l10n_br_fiscal_dfe.document"

    def _get_document_state_label(self):
        self.ensure_one()
        if self.fiscal_type != "cte":
            return super()._get_document_state_label()
        return dict(SITUACAO_CTE).get(self.document_state, self.document_state)

    def _cte_dfe_complete(self):
        """Return the complete DF-e record holding the CT-e XML."""
        self.ensure_one()
        complete = self._get_complete_dfe()
        if not complete or not complete.attachment_id:
            raise UserError(_("No complete DF-e found."))
        return complete

    def action_view_imported_document(self):
        """Open the invoice created from this DF-e.

        Falls back to the fiscal document itself when accounting is not
        installed, as this module does not depend on l10n_br_account.
        """
        self.ensure_one()
        document = self.fiscal_document_id
        moves = document.move_ids if "move_ids" in document._fields else document
        record = moves[:1] or document
        return {
            "type": "ir.actions.act_window",
            "res_model": record._name,
            "res_id": record.id,
            "view_mode": "form",
        }

    def import_document(self):
        if self.fiscal_type != "cte":
            return super().import_document()
        complete = self._cte_dfe_complete()
        if complete.schema_type not in CTE_IMPORTABLE_SCHEMAS:
            raise UserError(
                _(
                    "Only the CT-e (model 57) can be imported as a fiscal "
                    "document. This DF-e is a %(schema)s.",
                    schema=complete.schema_type,
                )
            )
        return {
            "name": _("Import CT-e XML"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_file": complete.attachment_id.with_context(
                    bin_size=False
                ).datas,
            },
        }

    def make_pdf(self):
        """Generate the DACTE PDF from the complete CT-e XML."""
        if self.fiscal_type != "cte":
            return super().make_pdf()
        self = self.sudo()
        complete = self._cte_dfe_complete()
        if complete.schema_type not in CTE_IMPORTABLE_SCHEMAS:
            raise UserError(
                _(
                    "The DACTE can only be generated for a CT-e (model 57). "
                    "This DF-e is a %(schema)s.",
                    schema=complete.schema_type,
                )
            )
        xml_bytes = base64.b64decode(
            complete.attachment_id.with_context(bin_size=False).datas
        )
        config = self.env["ir.actions.report"]._get_dacte_config(
            self._cte_dfe_logo(), self.company_id
        )
        dacte = Dacte(xml=xml_bytes, config=config)
        buf = BytesIO()
        dacte.output(buf)

        pdf_att = self.env["ir.attachment"].create(
            {
                "name": f"DACTE_{complete.access_key}.pdf",
                "datas": base64.b64encode(buf.getvalue()),
                "res_model": complete._name,
                "res_id": complete.id,
                "mimetype": "application/pdf",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{pdf_att.id}?download=true",
            "target": "self",
        }

    def _cte_dfe_logo(self):
        """Third-party document: same logo l10n_br_cte prints for them."""
        logo = self.company_id.logo_web
        if not logo:
            return False
        return BytesIO(base64.b64decode(logo))
