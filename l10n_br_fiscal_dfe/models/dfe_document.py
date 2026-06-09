# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import re
import zipfile
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nBrFiscalDfeDocument(models.Model):
    _name = "l10n_br_fiscal_dfe.document"
    _description = "Fiscal document from distribution service"
    _order = "id desc"

    _sql_constraints = [
        (
            "access_key_company_uniq",
            "unique(access_key, company_id)",
            "Document already exists.",
        ),
    ]

    access_key = fields.Char(size=44, required=True, index=True)
    fiscal_type = fields.Selection([("nfe", "NF-e"), ("cte", "CT-e")])
    dfe_ids = fields.One2many(
        "l10n_br_fiscal_dfe.dfe", "dfe_document_id", string="DF-e records"
    )

    emitter = fields.Char(size=60)
    vat = fields.Char(string="CNPJ/CPF", size=18)
    document_amount = fields.Float(string="Total Value", digits=(18, 2))
    document_state = fields.Char(string="State Code")
    document_number = fields.Char(size=18)
    document_emission_date = fields.Datetime(string="Emission Date")
    serie = fields.Char(size=3)

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company.id
    )
    partner_id = fields.Many2one(
        "res.partner", string="Partner", compute="_compute_partner_id", store=True
    )
    is_own_document = fields.Boolean(compute="_compute_is_own_document", store=True)

    color_status = fields.Selection(
        [("green", "Complete"), ("blue", "Summary"), ("muted", "Cancelled/Denied")],
        compute="_compute_color_status",
        store=True,
    )

    @api.depends("access_key")
    def _compute_partner_id(self):
        for record in self:
            key = record.access_key or ""
            if len(key) == 44:
                cnpj_digits = key[6:20]
                record.partner_id = self.env["res.partner"].search(
                    [("cnpj_cpf_stripped", "=", cnpj_digits)], limit=1
                )
            else:
                record.partner_id = False

    @api.depends("access_key", "company_id.vat")
    def _compute_is_own_document(self):
        for record in self:
            key = record.access_key or ""
            company_cnpj = re.sub("[^0-9]", "", record.company_id.vat or "")
            record.is_own_document = len(key) == 44 and key[6:20] == company_cnpj

    @api.depends("dfe_ids.document_type_dfe", "document_state")
    def _compute_color_status(self):
        for record in self:
            if record.document_state in ("2", "3"):  # Cancelled or Denied
                record.color_status = "muted"
                continue
            types = record.dfe_ids.mapped("document_type_dfe")
            if "complete" in types:
                record.color_status = "green"
            elif "summary" in types:
                record.color_status = "blue"
            else:
                record.color_status = False

    def name_get(self):
        return [(record.id, record.access_key) for record in self]

    def _update_metadata(self, vals, is_complete=False):
        if is_complete or not self.dfe_ids.filtered(
            lambda d: d.document_type_dfe == "complete"
        ):
            self.sudo().write(vals)

    def _get_complete_dfe(self):
        """Return the first complete DFe record or None."""
        self.ensure_one()
        return self.dfe_ids.filtered(lambda d: d.document_type_dfe == "complete")[:1]

    def import_document(self):
        """Import the document into the fiscal system.

        This method must be implemented by fiscal type specific modules
        (e.g., l10n_br_nfe_dfe for NF-e, l10n_br_cte_dfe for CT-e).

        Raises:
            NotImplementedError: If not implemented by a subclass.

        Returns:
            Recordset of the created fiscal document.
        """
        raise NotImplementedError(
            "import_document() must be implemented in fiscal type specific modules "
            "(e.g., l10n_br_nfe_dfe, l10n_br_cte_dfe)."
        )

    def make_pdf(self):
        """Generate PDF representation of the document.

        This method must be implemented by fiscal type specific modules
        (e.g., l10n_br_nfe_dfe for NF-e, l10n_br_cte_dfe for CT-e).

        Raises:
            NotImplementedError: If not implemented by a subclass.

        Returns:
            Action dict to download the PDF.
        """
        raise NotImplementedError(
            "make_pdf() must be implemented in fiscal type specific modules "
            "(e.g., l10n_br_nfe_dfe, l10n_br_cte_dfe)."
        )

    def action_match_partner(self):
        """Re-run the partner matching logic"""
        self.sudo()._compute_partner_id()

    def action_download_xmls_zip(self):
        """Download complete XMLs of selected documents as a zip file."""
        self = self.sudo()
        attachments = self.env["ir.attachment"]
        for doc in self:
            complete_dfe = doc.dfe_ids.filtered(
                lambda d: d.document_type_dfe == "complete"
            )[:1]
            if complete_dfe and complete_dfe.attachment_id:
                attachments |= complete_dfe.attachment_id

        if not attachments:
            raise UserError(_("No complete XML found in the selected documents."))

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for att in attachments:
                data = base64.b64decode(att.with_context(bin_size=False).datas or b"")
                if data:
                    zf.writestr(att.name or "unknown.xml", data)

        zip_attachment = self.env["ir.attachment"].create(
            {
                "name": "dfe_xmls.zip",
                "type": "binary",
                "datas": base64.b64encode(buf.getvalue()),
                "mimetype": "application/zip",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/{zip_attachment.id}/{zip_attachment.name}?download=true"
            ),
            "target": "self",
        }
