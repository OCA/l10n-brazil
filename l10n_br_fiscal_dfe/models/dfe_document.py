# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import re
import zipfile
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nBrFiscalDfeDocument(models.Model):
    """Generic DF-e document, grouped by access key.

    Fiscal document agnostic. Fiscal type specific behaviors (import,
    PDF generation, manifestation...) are implemented by inheritance in
    modules such as l10n_br_nfe_dfe or l10n_br_cte_dfe.
    """

    _name = "l10n_br_fiscal_dfe.document"
    _description = "Fiscal document from distribution service"
    _order = "id desc"

    _sql_constraints = [
        (
            "access_key_company_uniq",
            "unique(access_key, company_id)",
            "A DFe with this access key already exists for this company.",
        ),
    ]

    access_key = fields.Char(size=44, required=True, index=True)

    fiscal_type = fields.Selection(
        selection=[("nfe", "NF-e"), ("cte", "CT-e")],
        index=True,
    )

    dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal_dfe.dfe",
        inverse_name="dfe_document_id",
        string="DF-e records",
    )

    emitter = fields.Char(size=60)

    vat = fields.Char(string="CNPJ/CPF", size=18)

    document_amount = fields.Float(string="Document Total Value", digits=(18, 2))

    document_state = fields.Char(
        string="State Code",
        help="Document situation code as received from the distribution "
        "service (semantics depend on the fiscal document type).",
    )

    document_number = fields.Char(size=18)

    document_emission_date = fields.Datetime(string="Emission Date")

    serie = fields.Char(size=3)

    color_status = fields.Selection(
        [
            ("green", "Complete"),
            ("blue", "Summary"),
            ("muted", "Cancelled/Denied"),
        ],
        compute="_compute_color_status",
        store=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company.id,
        index=True,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        compute="_compute_partner_id",
        store=True,
    )

    is_own_document = fields.Boolean(
        string="Own Document",
        compute="_compute_is_own_document",
        store=True,
        help="True when the emitter CNPJ in the access key matches the company CNPJ.",
    )

    @api.depends("access_key")
    def _compute_partner_id(self):
        Partner = self.env["res.partner"]
        for record in self:
            key = record.access_key or ""
            if len(key) == 44:
                cnpj_digits = key[6:20]
                partner = Partner.search(
                    [("cnpj_cpf_stripped", "=", cnpj_digits)],
                    limit=1,
                )
                record.partner_id = partner
            else:
                record.partner_id = False

    def action_match_partner(self):
        """Re-run the partner matching logic"""
        self.sudo()._compute_partner_id()

    @api.depends("access_key", "company_id.vat")
    def _compute_is_own_document(self):
        for record in self:
            key = record.access_key or ""
            company_cnpj = re.sub("[^0-9]", "", record.company_id.vat or "")
            if len(key) == 44 and company_cnpj:
                record.is_own_document = key[6:20] == company_cnpj
            else:
                record.is_own_document = False

    @api.depends("dfe_ids.document_type_dfe", "document_state")
    def _compute_color_status(self):
        for record in self:
            if record.document_state in ("2", "3"):
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
        """Update document metadata from parsed XML data.

        Complete payloads (is_complete=True) always overwrite.
        Summaries only write if no complete dfe exists yet.
        """
        if is_complete or not self.dfe_ids.filtered(
            lambda dfe: dfe.document_type_dfe == "complete"
        ):
            self.sudo().write(vals)

    def _get_complete_dfe(self):
        """Return the first complete DFe record (if any)."""
        self.ensure_one()
        return self.dfe_ids.filtered(lambda d: d.document_type_dfe == "complete")[:1]

    def action_download_xml(self):
        self = self.sudo()
        self.ensure_one()
        complete_dfe = self._get_complete_dfe()
        if not complete_dfe:
            raise UserError(
                _("It is only possible to download XML when DF-e is completed.")
            )
        return complete_dfe.action_download_xml()

    def action_download_xmls_zip(self):
        """Download complete XMLs of selected documents as a zip file."""
        self = self.sudo()
        attachments = self.env["ir.attachment"]
        for doc in self:
            complete_dfe = doc._get_complete_dfe()
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
                f"/web/content/{zip_attachment.id}"
                f"/{zip_attachment.name}?download=true"
            ),
            "target": "self",
        }

    def import_document(self):
        """Import the document into the fiscal system.

        Must be implemented by fiscal type specific modules
        (e.g., l10n_br_nfe_dfe for NF-e, l10n_br_cte_dfe for CT-e).
        """
        raise NotImplementedError(
            "import_document() must be implemented in fiscal type specific modules "
            "(e.g., l10n_br_nfe_dfe, l10n_br_cte_dfe)."
        )

    def make_pdf(self):
        """Generate a PDF representation of the document.

        Must be implemented by fiscal type specific modules
        (e.g., l10n_br_nfe_dfe for NF-e, l10n_br_cte_dfe for CT-e).
        """
        raise NotImplementedError(
            "make_pdf() must be implemented in fiscal type specific modules "
            "(e.g., l10n_br_nfe_dfe, l10n_br_cte_dfe)."
        )
