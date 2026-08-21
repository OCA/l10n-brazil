# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from lxml import etree

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NFSE_NACIONAL_NAMESPACE = {
    "nfse": "http://www.sped.fazenda.gov.br/nfse",
}


class DocumentImportNfseNacionalWizard(models.TransientModel):
    _name = "l10n_br_nfse_nacional.import.wizard"
    _description = "Import NFS-e Nacional (SEFIN XML)"

    xml_file = fields.Binary(
        string="NFS-e Nacional XML File",
        required=True,
    )
    xml_filename = fields.Char(string="File Name")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        readonly=True,
    )

    def action_import(self):
        """Parse the uploaded XML and create or locate the matching fiscal document.

        Returns:
            dict: Action to open the resulting l10n_br_fiscal.document record.

        Raises:
            UserError: When the file is missing or the XML is malformed.
        """
        self.ensure_one()
        if not self.xml_file:
            raise UserError(_("Please select an XML file."))

        try:
            xml_bytes = base64.b64decode(self.xml_file)
        except Exception as e:
            raise UserError(_("Could not decode the uploaded file: %s") % str(e)) from e

        nfse_data = self._parse_nfse_nacional_xml(xml_bytes)
        document = self._find_or_create_document(nfse_data)
        self.document_id = document

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document",
            "res_id": document.id,
            "view_mode": "form",
            "target": "current",
        }

    def _parse_nfse_nacional_xml(self, xml_bytes):
        """Parse the NFS-e Nacional XML and return a dict of relevant fields.

        Tries namespace-aware XPath first, then falls back to plain tag names
        to handle both namespaced and non-namespaced XML variants.

        Args:
            xml_bytes (bytes): Raw XML content from the uploaded file.

        Returns:
            dict: Extracted fields plus 'xml_raw' for the original bytes.

        Raises:
            UserError: When the XML is syntactically invalid.
        """
        try:
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as e:
            raise UserError(_("Invalid XML: %s") % str(e)) from e

        def _text(xpath):
            elements = root.xpath(xpath, namespaces=NFSE_NACIONAL_NAMESPACE)
            return elements[0].text.strip() if elements and elements[0].text else ""

        return {
            "numero": _text(".//nfse:Numero") or _text(".//Numero"),
            "chave": _text(".//nfse:ChaveAcesso") or _text(".//ChaveAcesso"),
            "data_emissao": _text(".//nfse:DtHrEmit") or _text(".//DtHrEmit"),
            "codigo_verificacao": (_text(".//nfse:CodVerif") or _text(".//CodVerif")),
            "cnpj_prestador": (
                _text(".//nfse:CNPJ[parent::nfse:Prest]")
                or _text(".//CNPJ[parent::Prest]")
                or _text(".//nfse:CNPJ")
                or _text(".//CNPJ")
            ),
            "razao_social_prestador": (
                _text(".//nfse:xNome[parent::nfse:Prest]")
                or _text(".//xNome[parent::Prest]")
                or _text(".//nfse:xNome")
                or _text(".//xNome")
            ),
            "cnpj_tomador": (
                _text(".//nfse:CNPJ[parent::nfse:Toma]")
                or _text(".//CNPJ[parent::Toma]")
            ),
            "razao_social_tomador": (
                _text(".//nfse:xNome[parent::nfse:Toma]")
                or _text(".//xNome[parent::Toma]")
            ),
            "valor_servicos": _text(".//nfse:vServ") or _text(".//vServ"),
            "descricao": _text(".//nfse:xDisc") or _text(".//xDisc"),
            "valor_iss": _text(".//nfse:vISS") or _text(".//vISS"),
            "xml_raw": xml_bytes,
        }

    def _find_or_create_partner(self, cnpj_cpf, company_name):
        """Look up a partner by CNPJ/CPF digits, creating one if not found.

        Args:
            cnpj_cpf (str): CNPJ or CPF digits (no formatting).
            company_name (str): Legal name used when creating a new partner.

        Returns:
            res.partner: Singleton or empty recordset.
        """
        if not cnpj_cpf:
            return self.env["res.partner"]

        partner = self.env["res.partner"].search([("vat", "=", cnpj_cpf)], limit=1)
        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": company_name or cnpj_cpf,
                    "cnpj_cpf": cnpj_cpf,
                    "company_type": "company",
                    "country_id": self.env.ref("base.br").id,
                }
            )
        return partner

    def _find_or_create_document(self, nfse_data):
        """Return an existing document matching the NFS-e, or create a new one.

        Matches by NFS-e Nacional access key first, then by document number.
        When no match is found, creates a new l10n_br_fiscal.document in
        AUTORIZADA state and attaches the original XML.

        Args:
            nfse_data (dict): Parsed NFS-e data from _parse_nfse_nacional_xml().

        Returns:
            l10n_br_fiscal.document: The found or newly created document.
        """
        from odoo.addons.l10n_br_fiscal.constants.fiscal import (
            MODELO_FISCAL_NFSE,
            SITUACAO_EDOC_AUTORIZADA,
        )

        access_key = nfse_data.get("chave", "")
        numero = nfse_data.get("numero", "")

        domain = [("company_id", "=", self.company_id.id)]
        if access_key:
            domain.append(("nfse_nacional_chave", "=", access_key))
        elif numero:
            domain.append(("document_number", "=", numero))

        document = (
            self.env["l10n_br_fiscal.document"].search(domain, limit=1)
            if (access_key or numero)
            else self.env["l10n_br_fiscal.document"]
        )

        if document:
            return document

        partner = self._find_or_create_partner(
            nfse_data.get("cnpj_prestador", ""),
            nfse_data.get("razao_social_prestador", ""),
        )

        document_type = self.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", MODELO_FISCAL_NFSE)], limit=1
        )

        document_serie = self.env["l10n_br_fiscal.document.serie"].search(
            [
                ("document_type_id", "=", document_type.id if document_type else False),
                ("company_id", "in", [self.company_id.id, False]),
                ("active", "=", True),
            ],
            limit=1,
        )

        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company_id.id,
                "partner_id": partner.id,
                "document_type_id": document_type.id if document_type else False,
                "document_serie_id": document_serie.id if document_serie else False,
                "document_number": numero,
                "verify_code": nfse_data.get("codigo_verificacao", ""),
                "nfse_nacional_chave": access_key,
                "state_edoc": SITUACAO_EDOC_AUTORIZADA,
            }
        )

        xml_bytes = nfse_data.get("xml_raw", b"")
        if xml_bytes:
            self.env["ir.attachment"].create(
                {
                    "name": f"NFS-e-Nacional-{numero or access_key}.xml",
                    "res_model": "l10n_br_fiscal.document",
                    "res_id": document.id,
                    "datas": base64.b64encode(xml_bytes),
                    "mimetype": "text/xml",
                    "type": "binary",
                }
            )

        return document
