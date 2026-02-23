# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
import re
import zipfile
from io import BytesIO

from brazilfiscalreport.danfe import Danfe
from lxml import objectify

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.dfe import SITUACAO_NFE

_logger = logging.getLogger(__name__)


class L10nBrFiscalDfeDocument(models.Model):
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

    dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal_dfe.dfe",
        inverse_name="dfe_document_id",
        string="DF-e records",
    )

    emitter = fields.Char(size=60)

    vat = fields.Char(string="CNPJ/CPF", size=18)

    document_amount = fields.Float(string="Document Total Value", digits=(18, 2))

    document_state = fields.Selection(
        selection=SITUACAO_NFE,
    )

    document_number = fields.Char(size=18)

    document_emission_date = fields.Datetime(string="Emission Date")

    serie = fields.Char(size=3)

    color_status = fields.Selection(
        [
            ("green", "NF-e Completa"),
            ("blue", "Resumo da NF-e"),
            ("muted", "Cancelada/Denegada"),
        ],
        compute="_compute_color_status",
        store=True,
    )

    manifestation_status = fields.Selection(
        selection=[
            ("ciente", "Ciente da Operação"),
            ("confirmado", "Confirmada operação"),
            ("desconhecido", "Desconhecimento"),
            ("nao_realizado", "Não realizado"),
            ("sem_manifestacao", "Sem manifestação"),
        ],
        compute="_compute_manifestation_status",
    )

    manifestations_ids = fields.One2many(
        comodel_name="l10n_br_nfe.md_event",
        compute="_compute_manifestations_ids",
        string="Manifestations",
    )

    cfop_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOPs",
        compute="_compute_cfop_ids",
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

    @api.depends("dfe_ids.attachment_id")
    def _compute_cfop_ids(self):
        Cfop = self.env["l10n_br_fiscal.cfop"]
        for record in self:
            record.cfop_ids = Cfop
            complete_dfe = record.dfe_ids.filtered(
                lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
            )
            if not complete_dfe:
                continue
            data = complete_dfe[0].attachment_id.with_context(bin_size=False).datas
            if not data:
                continue
            try:
                xml_bytes = base64.b64decode(data)
                root = objectify.fromstring(xml_bytes)
                cfop_codes = set()
                for det in root.NFe.infNFe.det:
                    cfop_codes.add(str(det.prod.CFOP))
                if cfop_codes:
                    record.cfop_ids = Cfop.search([("code", "in", list(cfop_codes))])
            except Exception:
                _logger.debug("Could not extract CFOPs from document %s XML", record.id)

    def _update_metadata(self, vals, is_complete=False):
        """Update document metadata from parsed XML data.

        procNFe (is_complete=True) always overwrites.
        resNFe only writes if no complete dfe exists yet.
        """
        if is_complete or not self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        ):
            self.sudo().write(vals)

    def _compute_manifestation_status(self):
        for record in self:
            latest = self.env["l10n_br_nfe.md_event"].search(
                [
                    ("access_key", "=", record.access_key),
                    ("state", "=", "done"),
                ],
                order="id desc",
                limit=1,
            )
            record.manifestation_status = (
                latest.event_type if latest else "sem_manifestacao"
            )

    @api.depends("access_key")
    def _compute_manifestations_ids(self):
        for record in self:
            manifestations = self.env["l10n_br_nfe.md_event"].search(
                [("access_key", "=", record.access_key)]
            )
            record.manifestations_ids = manifestations

    @api.depends("dfe_ids.dfe_nfe_document_type", "document_state")
    def _compute_color_status(self):
        for record in self:
            if record.document_state in ("2", "3"):
                record.color_status = "muted"
                continue
            types = record.dfe_ids.mapped("dfe_nfe_document_type")
            if "dfe_nfe_complete" in types:
                record.color_status = "green"
            elif "dfe_nfe_summary" in types:
                record.color_status = "blue"
            else:
                record.color_status = False

    def name_get(self):
        return [(record.id, record.access_key) for record in self]

    def action_download_xml(self):
        self = self.sudo()
        self.ensure_one()
        complete_dfe = self.dfe_ids.filtered(
            lambda d: d.dfe_nfe_document_type == "dfe_nfe_complete"
        )[:1]
        if not complete_dfe:
            raise UserError(
                _("It is only possible to download XML when DF-e is completed.")
            )
        return complete_dfe.action_download_xml()

    def action_download_xmls_zip(self):
        """Download complete NF-e XMLs of selected documents as a zip file."""
        self = self.sudo()
        attachments = self.env["ir.attachment"]
        for doc in self:
            complete_dfe = doc.dfe_ids.filtered(
                lambda d: d.dfe_nfe_document_type == "dfe_nfe_complete"
            )[:1]
            if complete_dfe and complete_dfe.attachment_id:
                attachments |= complete_dfe.attachment_id
        if not attachments:
            raise UserError(_("No complete NF-e XML found in the selected documents."))

        buf = BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for att in attachments:
                data = base64.b64decode(att.with_context(bin_size=False).datas or b"")
                if data:
                    zf.writestr(att.name or "unknown.xml", data)

        zip_attachment = self.env["ir.attachment"].create(
            {
                "name": "nfe_xmls.zip",
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

    def make_pdf(self):
        self = self.sudo()
        complete_dfe_ids = self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        )

        if not complete_dfe_ids:
            raise UserError(_("No DF-e with 'DF-e complete' type found."))

        complete_dfe = complete_dfe_ids[0]
        attachment = complete_dfe.attachment_id
        nfe_xml = base64.b64decode(attachment.datas)
        danfe = Danfe(xml=nfe_xml)

        tmp_danfe = BytesIO()
        danfe.output(tmp_danfe)
        danfe_file = tmp_danfe.getvalue()
        tmp_danfe.close()

        pdf_attachment = self.env["ir.attachment"].create(
            {
                "name": f"DANFE{complete_dfe.access_key}.pdf",
                "type": "binary",
                "datas": base64.b64encode(danfe_file),
                "res_model": self._name,
                "res_id": complete_dfe.id,
                "mimetype": "application/pdf",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{pdf_attachment.id}?download=true",
            "target": "self",
        }

    def create_nfe_md_action(self):
        self.ensure_one()
        return {
            "name": _("Manifestação do Destinatário da NF-e"),
            "type": "ir.actions.act_window",
            "res_model": "nfe_recipient_manifestation_event.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_access_key": self.access_key,
            },
        }

    def import_document(self):
        complete_dfe = self.dfe_ids.filtered(
            lambda dfe: dfe.dfe_nfe_document_type == "dfe_nfe_complete"
        )[:1]
        if not complete_dfe or not complete_dfe.attachment_id:
            raise UserError(
                _("You can only import the NF-e when the DF-e is completed.")
            )
        xml_bytes = base64.b64decode(
            complete_dfe.attachment_id.with_context(bin_size=False).datas
        )
        xml_stream = BytesIO(xml_bytes)
        parse_method_name = f"parse_{complete_dfe.schema_type}"
        parse_method = getattr(self.company_id, parse_method_name, None)
        if not parse_method:
            raise UserError(
                _(
                    "No import method available for schema type '%(schema)s'.",
                    schema=complete_dfe.schema_type,
                )
            )
        return parse_method(xml_stream)
