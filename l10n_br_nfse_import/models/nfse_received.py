# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import datetime
import gzip
import logging

from lxml import etree

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class NfseReceived(models.Model):
    """Received NFS-e pending review and import as a fiscal document.

    Each record represents an NFS-e issued by a third party (prestador)
    where the company is the tomador (service recipient). After syncing
    from a fetch engine the user reviews the record and confirms the import,
    which creates the corresponding l10n_br_fiscal.document.
    """

    _name = "l10n_br_nfse.received"
    _description = "Received NFS-e"
    _order = "emission_date desc, id desc"
    _rec_name = "nfse_number"

    dfe_id = fields.Many2one(
        comodel_name="l10n_br_nfse.dfe",
        string="Fetch Engine",
        ondelete="set null",
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    nfse_number = fields.Char(string="NFS-e Number", index=True)
    verify_code = fields.Char(string="Verification Code")
    emission_date = fields.Datetime(string="Emission Date")
    document_serie = fields.Char(string="Document Serie")
    rps_number = fields.Char(string="RPS / DPS Number")

    provider_cnpj = fields.Char(string="Provider CNPJ")
    provider_name = fields.Char(string="Provider Name")
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        compute="_compute_partner_id",
        store=True,
        help="Resolved from the provider CNPJ. Can be overridden in the import wizard.",
    )

    service_value = fields.Float(string="Service Value", digits=(18, 2))
    service_description = fields.Text(string="Service Description")
    fiscal_additional_data = fields.Text(string="Additional Info")

    issqn_base = fields.Float(string="ISSQN Base", digits=(18, 2))
    issqn_percent = fields.Float(string="ISSQN %")
    issqn_value = fields.Float(string="ISSQN Value", digits=(18, 2))
    issqn_wh_percent = fields.Float(string="ISSQN Ret. %")
    issqn_wh_value = fields.Float(string="ISSQN Ret. Value", digits=(18, 2))

    service_lc116_code = fields.Char(
        string="LC116 Code",
        help="LC 116 service code extracted from the XML (cTribNac / cServLC116).",
    )
    service_nbs_code = fields.Char(
        string="NBS Code",
        help="NBS code extracted from the XML (cNBS), digits only.",
    )
    issqn_city_ibge = fields.Char(
        string="Service City IBGE",
        help="IBGE code of the municipality where ISSQN is due (cLocIncid).",
    )
    civil_construction_code = fields.Char(string="Civil Construction Code")
    civil_construction_art = fields.Char(string="Civil Construction ART")

    state = fields.Selection(
        selection=[
            ("pending", "Pending Review"),
            ("done", "Imported"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="pending",
        required=True,
        index=True,
        tracking=True,
    )

    account_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Vendor Bill",
        readonly=True,
    )
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        readonly=True,
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="XML Attachment",
        readonly=True,
    )

    @api.depends("provider_cnpj")
    def _compute_partner_id(self):
        """Resolve partner from provider CNPJ using exact formatted or digit match."""
        for rec in self:
            if not rec.provider_cnpj:
                rec.partner_id = False
                continue
            digits = "".join(c for c in rec.provider_cnpj if c.isdigit())
            if not digits:
                rec.partner_id = False
                continue
            if len(digits) == 14:
                formatted = "%s.%s.%s/%s-%s" % (
                    digits[:2],
                    digits[2:5],
                    digits[5:8],
                    digits[8:12],
                    digits[12:],
                )
                domain = ["|", ("cnpj_cpf", "=", formatted), ("cnpj_cpf", "=", digits)]
            else:
                domain = [("cnpj_cpf", "=", digits)]
            rec.partner_id = self.env["res.partner"].search(domain, limit=1)

    def action_view_vendor_bill(self):
        """Open the linked vendor bill."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vendor Bill"),
            "res_model": "account.move",
            "res_id": self.account_move_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_import_wizard(self):
        """Open the review wizard to import this NFS-e as a fiscal document."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Import NFS-e"),
            "res_model": "l10n_br_nfse.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_received_id": self.id,
                "default_company_id": self.company_id.id,
            },
        }

    def action_cancel(self):
        """Cancel pending records without creating a fiscal document."""
        self.filtered(lambda r: r.state == "pending").write({"state": "cancelled"})

    def action_reset_to_pending(self):
        """Revert cancelled records back to pending for review."""
        self.filtered(lambda r: r.state == "cancelled").write({"state": "pending"})

    def action_reparse_xml(self):
        """Re-read the XML attachment and refresh all extracted fields."""
        for rec in self:
            if not rec.attachment_id:
                continue
            try:
                rec._parse_and_write_xml(rec.attachment_id.datas)
            except Exception as exc:
                _logger.warning("reparse_xml failed for received %s: %s", rec.id, exc)

    @staticmethod
    def _text_xpath(root, *xpaths):
        """Find the first matching non-empty text node across XPaths."""
        for xp in xpaths:
            el = root.find(xp)
            if el is not None and el.text:
                return el.text.strip()
        return None

    def _extract_xml_financials(self, root, vals):
        """Extract pricing, tax base, and ISSQN values from the XML."""
        t = self._text_xpath
        val = t(
            root,
            ".//vServPrest/vServ",
            ".//vServPrest/vReceb",
            ".//vBC",
            ".//vNFSe",
            ".//vServicos",
            ".//ValorServicos",
            ".//ValorTotal",
            ".//vLiq",
        )
        desc = t(
            root,
            ".//cServ/xDescServ",
            ".//xDescServ",
            ".//xDiscriminacao",
            ".//Discriminacao",
            ".//DescricaoServico",
        )
        vbc = t(root, ".//valores/vBC", ".//vBC")
        paliq = t(root, ".//pAliqAplic", ".//Aliquota", ".//aliquota")
        vissqn = t(root, ".//vISSQN", ".//ValorIss", ".//valorIss")
        vwh = t(root, ".//ValorIssRetido", ".//valorIssRetido")
        tp_ret = t(root, ".//tpRetISSQN", ".//IssRetido")

        if val:
            vals["service_value"] = float(val)
        if desc:
            vals["service_description"] = desc
        if vbc:
            vals["issqn_base"] = float(vbc)
        if vissqn:
            vals["issqn_value"] = float(vissqn)
        if paliq:
            paliq_f = float(paliq)
            vals["issqn_percent"] = paliq_f
            if tp_ret == "1":
                vals["issqn_wh_percent"] = paliq_f
        if vwh:
            vals["issqn_wh_value"] = float(vwh)
        elif tp_ret == "1" and vissqn:
            vals["issqn_wh_value"] = float(vissqn)

    def _extract_xml_codes(self, root, vals):
        """Extract legal codes, series, and operational identifiers."""
        t = self._text_xpath
        lc116 = t(root, ".//cTribNac", ".//cServLC116", ".//ItemListaServico")
        nbs = t(root, ".//cNBS", ".//CodigoNbs")
        ibge = t(root, ".//cLocIncid", ".//cLocPrestacao", ".//CodigoMunicipio")
        serie = t(root, ".//serie", ".//Serie")
        ndps = t(root, ".//nDPS", ".//NumeroRps", ".//Numero")
        xnome_trib = t(root, ".//xTribNac", ".//xServicos")
        cobr = t(root, ".//cObra", ".//CodigoObra")
        art = t(root, ".//art", ".//Art", ".//ArtObra")
        inf_compl = t(
            root,
            ".//xInfComp",
            ".//InformacoesComplementares",
            ".//InfComplementares",
        )

        if lc116:
            vals["service_lc116_code"] = lc116.strip()
        if nbs:
            vals["service_nbs_code"] = "".join(c for c in nbs if c.isdigit())
        if ibge:
            vals["issqn_city_ibge"] = "".join(c for c in ibge if c.isdigit())
        if serie:
            vals["document_serie"] = serie.strip()
        if ndps:
            vals["rps_number"] = ndps.strip()
        if cobr:
            vals["civil_construction_code"] = cobr.strip()
        if art:
            vals["civil_construction_art"] = art.strip()

        extra_parts = [p for p in [xnome_trib, inf_compl] if p]
        if extra_parts:
            vals["fiscal_additional_data"] = "\n".join(extra_parts)

    def _extract_xml_dates_and_verify(self, root, vals):
        """Extract processing timestamps and access keys/verification codes."""
        t = self._text_xpath
        dt_text = t(root, ".//dhEmi", ".//DataEmissao")
        inf_nfse = root.find(".//infNFSe") or root.find(".//InfNfse")
        xml_chave = (inf_nfse.get("Id") if inf_nfse is not None else None) or ""

        if dt_text:
            try:
                vals["emission_date"] = datetime.datetime.fromisoformat(
                    dt_text[:19].replace("T", " ")
                )
            except Exception:
                pass

        current_vc = self.verify_code or ""
        if xml_chave and (not current_vc or current_vc.isdigit()):
            vals["verify_code"] = xml_chave

    def _parse_and_write_xml(self, datas_b64):
        """Decode, parse and write extractable fields from a b64 NFS-e XML."""
        raw = base64.b64decode(datas_b64)
        try:
            xml_bytes = gzip.decompress(raw)
        except Exception:
            xml_bytes = raw

        root = etree.fromstring(xml_bytes)
        for node in root.iter():
            if "}" in node.tag:
                node.tag = node.tag.split("}", 1)[1]

        vals = {}
        self._extract_xml_financials(root, vals)
        self._extract_xml_codes(root, vals)
        self._extract_xml_dates_and_verify(root, vals)

        if vals:
            self.write(vals)

    def _create_xml_attachment(self, xml_content):
        """Store the NFS-e XML as an ir.attachment linked to this record."""
        self.ensure_one()
        xml_bytes = (
            xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "NFSe-%s.xml" % (self.nfse_number or "received"),
                "datas": base64.b64encode(xml_bytes).decode("ascii"),
                "description": "Received NFS-e XML",
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        self.attachment_id = attachment
        return attachment
