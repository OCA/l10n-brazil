# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import re
import zipfile
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Model of the document (positions 21 and 22 of the access key) -> fiscal type
FISCAL_TYPE_BY_MODEL = {"55": "nfe", "57": "cte"}


class L10nBrFiscalDfeDocument(models.Model):
    """Generic DF-e document, grouped by access key.

    Fiscal document agnostic. Fiscal type specific behaviors (import,
    PDF generation, manifestation...) are implemented by inheritance in
    modules such as l10n_br_nfe_dfe or l10n_br_cte_dfe.
    """

    _name = "l10n_br_fiscal_dfe.document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fiscal document from distribution service"
    _order = "id desc"

    _sql_constraints = [
        (
            "access_key_company_uniq",
            "unique(access_key, company_id)",
            "A DFe with this access key already exists for this company.",
        ),
    ]

    access_key = fields.Char(size=50, required=True, index=True)

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

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency",
    )

    document_amount = fields.Monetary(string="Document Total Value")

    document_state = fields.Char(
        string="State Code",
        help="Document situation code as received from the distribution "
        "service (semantics depend on the fiscal document type).",
    )

    document_state_label = fields.Char(
        string="State",
        compute="_compute_document_state_label",
    )

    document_number = fields.Char(size=18)

    document_emission_date = fields.Datetime(string="Emission Date")

    # A national NFS-e DPS series has up to 5 characters (TSSerieDPS).
    serie = fields.Char(size=5)

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

    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        compute="_compute_fiscal_document_id",
        search="_search_fiscal_document_id",
        help="Fiscal document already imported with this access key.",
    )

    import_requested_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Import Requested By",
        help="User that asked to import this access key before the complete XML "
        "was here. The fiscal document is created when the XML arrives.",
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

    @api.depends("access_key", "company_id")
    def _compute_fiscal_document_id(self):
        """Link each inbox row to the fiscal document that shares its access key."""
        keys = [key for key in self.mapped("access_key") if key]
        grouped = {}
        if keys:
            matches = self.env["l10n_br_fiscal.document"].search(
                [("document_key", "in", keys)]
            )
            for document in matches:
                grouped.setdefault(
                    document.document_key, self.env["l10n_br_fiscal.document"]
                )
                grouped[document.document_key] |= document
        empty = self.env["l10n_br_fiscal.document"]
        for record in self:
            candidates = grouped.get(record.access_key, empty)
            record.fiscal_document_id = record._match_fiscal_document(candidates)

    def _match_fiscal_document(self, candidates):
        """Return the fiscal document imported from this inbox row.

        ``candidates`` already share this access key. The default keeps the
        document of the same company. A fiscal-type module overrides this
        when its match differs and may ignore ``candidates``.
        """
        self.ensure_one()
        same_company = candidates.filtered(
            lambda document, company=self.company_id: document.company_id == company
        )
        return (same_company or candidates)[:1]

    def _search_fiscal_document_id(self, operator, value):
        """Inbox rows whose access key is already a fiscal document key."""
        if operator in ("=", "!=") and not value:
            key_operator = "not in" if operator == "=" else "in"
            return [("access_key", key_operator, self._imported_access_keys())]
        fiscal_documents = self.env["l10n_br_fiscal.document"]
        if operator in ("=", "in"):
            ids = value if operator == "in" else [value]
            keys = fiscal_documents.browse([item for item in ids if item]).mapped(
                "document_key"
            )
            return [("access_key", "in", keys)]
        if operator in ("!=", "not in"):
            ids = value if operator == "not in" else [value]
            keys = fiscal_documents.browse([item for item in ids if item]).mapped(
                "document_key"
            )
            return [("access_key", "not in", keys)]
        raise UserError(_("Operation not supported"))

    def _imported_access_keys(self):
        return (
            self.env["l10n_br_fiscal.document"]
            .search([("document_key", "!=", False)])
            .mapped("document_key")
        )

    @api.depends("access_key", "company_id.vat")
    def _compute_is_own_document(self):
        for record in self:
            key = record.access_key or ""
            company_cnpj = re.sub("[^0-9]", "", record.company_id.vat or "")
            if len(key) == 44 and company_cnpj:
                record.is_own_document = key[6:20] == company_cnpj
            else:
                record.is_own_document = False

    @api.depends("document_state", "fiscal_type")
    def _compute_document_state_label(self):
        for record in self:
            record.document_state_label = record._get_document_state_label()

    def _get_document_state_label(self):
        """Human-readable label for ``document_state``.

        The raw code's meaning depends on the fiscal document type, so
        fiscal type specific modules (e.g. l10n_br_nfe_dfe) should
        override this to map their own status codes to readable text.
        Defaults to the raw code when no mapping is available.
        """
        self.ensure_one()
        return self.document_state

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
                f"/web/content/{zip_attachment.id}/{zip_attachment.name}?download=true"
            ),
            "target": "self",
        }

    @api.model
    def _dfe_fiscal_type_from_key(self, access_key):
        """Fiscal type of the document that has this access key."""
        fiscal_type = FISCAL_TYPE_BY_MODEL.get(access_key[20:22])
        if not fiscal_type:
            raise UserError(
                _("Only NF-e (model 55) and CT-e (model 57) can be imported by key.")
            )
        return fiscal_type

    def _dfe_import_block_reason(self):
        """Why the document cannot be imported, or False."""
        self.ensure_one()
        if self.document_state == "3":
            return _("This note was cancelled by the issuer.")
        if self.document_state == "2":
            return _("This note was denied by the tax authority.")
        return False

    def import_document(self):
        """Import the document into the fiscal system: from the complete XML, or,
        when only the summary is here, asking for the XML first."""
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group("l10n_br_fiscal.group_user")):
            raise UserError(
                _("Only the fiscal users can import a document from the inbox.")
            )
        return (
            self.env["l10n_br_fiscal_edi.document.import.wizard"]
            .create({"dfe_document_id": self.id})
            .action_import()
        )

    def action_view_imported_document(self):
        """Open the fiscal document created from this note.

        It is the document of the import, whatever the type of the note, and not the
        invoice of it: whoever imports is a fiscal user and may have no access to
        accounting. The companies of the note go in the context, so that it opens
        also for a user whose company switcher does not have it on.
        """
        self.ensure_one()
        document = self.fiscal_document_id
        allowed = list(self.env.context.get("allowed_company_ids") or [])
        allowed = allowed or self.env.companies.ids
        allowed += [cid for cid in document.company_id.ids if cid not in allowed]
        return {
            "type": "ir.actions.act_window",
            "res_model": document._name,
            "res_id": document.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "context": {"allowed_company_ids": allowed},
        }

    def _dfe_import_confirmation_message(self):
        """What the user must confirm before the complete XML is asked for, or
        False when nothing has to be confirmed."""
        self.ensure_one()
        return False

    def _dfe_import_request(self):
        """Ask for the complete XML of a document that only has the summary. A
        fiscal type that can release it overrides this."""
        self.ensure_one()
        raise UserError(
            _(
                "The complete XML of this document is not available. Upload its "
                "XML file instead."
            )
        )

    def _dfe_import_requested_xml(self):
        """Create the fiscal document of an import asked by access key, now that
        the complete XML is here. It runs as who asked, so the author is kept."""
        self.ensure_one()
        user = self.import_requested_user_id
        attachment = self._get_complete_dfe().attachment_id
        if not user or not attachment:
            return
        self.sudo().import_requested_user_id = False
        attachment = attachment.with_context(bin_size=False)
        documents, errors, _warnings = (
            self.env["l10n_br_fiscal.document"]
            .with_user(user)
            .with_context(allowed_company_ids=self.company_id.ids, lang=user.lang)
            ._edi_import_files([(attachment.name, attachment.raw)], dfe_document=self)
        )
        for document in documents:
            document.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=user.id,
                note=_("Document created from the access key %s.") % self.access_key,
            )
        for _file, message in errors:
            self.company_id._dfe_log(
                message, log_type="error", fiscal_type=self.fiscal_type
            )
        if errors:
            self.sudo().activity_schedule(
                "mail.mail_activity_data_warning",
                user_id=user.id,
                summary=_("The note could not be imported"),
                note="\n".join(message for _file, message in errors),
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
