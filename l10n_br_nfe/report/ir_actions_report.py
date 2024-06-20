# Copyright 2024 Engenere.one
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
from io import BytesIO

from brazilfiscalreport.danfe import Danfe, DanfeConfig, InvoiceDisplay, Margins
from erpbrasil.edoc.pdf import base
from lxml import etree

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def temp_xml_autorizacao(self, xml_string):
        """TODO: Migrate-me to erpbrasil.edoc.pdf ASAP"""
        root = etree.fromstring(xml_string)
        ns = {None: "http://www.portalfiscal.inf.br/nfe"}
        new_root = etree.Element("nfeProc", nsmap=ns)

        protNFe_node = etree.Element("protNFe")
        infProt = etree.SubElement(protNFe_node, "infProt")
        etree.SubElement(infProt, "tpAmb").text = "2"
        etree.SubElement(infProt, "verAplic").text = ""
        etree.SubElement(infProt, "dhRecbto").text = None
        etree.SubElement(infProt, "nProt").text = ""
        etree.SubElement(infProt, "digVal").text = ""
        etree.SubElement(infProt, "cStat").text = ""
        etree.SubElement(infProt, "xMotivo").text = ""

        new_root.append(root)
        new_root.append(protNFe_node)
        return etree.tostring(new_root)

    def _render_qweb_html(self, res_ids, data=None):
        if self.report_name == "main_template_danfe":
            return

        return super()._render_qweb_html(res_ids, data=data)

    def _render_qweb_pdf(self, res_ids, data=None):
        if self.report_name not in ["main_template_danfe"]:
            return super()._render_qweb_pdf(res_ids, data=data)

        nfe = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])

        return self._render_danfe(nfe)

    def _render_danfe(self, nfe):
        if nfe.document_type != "55":
            raise UserError(_("You can only print a DANFE of a NFe(55)."))

        nfe_xml = False
        if nfe.authorization_file_id:
            nfe_xml = base64.b64decode(nfe.authorization_file_id.datas)
        elif nfe.send_file_id:
            nfe_xml = base64.b64decode(nfe.send_file_id.datas)

        if not nfe_xml:
            raise UserError(_("No xml file was found."))

        if nfe.company_id.danfe_library == "erpbrasil.edoc.pdf":
            nfe_xml = self.temp_xml_autorizacao(nfe_xml)
            return self.render_danfe_erpbrasil(nfe_xml)
        elif nfe.company_id.danfe_library == "brazil_fiscal_report":
            return self.render_danfe_brazilfiscalreport(nfe, nfe_xml)

    def render_danfe_brazilfiscalreport(self, nfe, nfe_xml):
        logo = False
        if nfe.issuer == "company" and nfe.company_id.logo:
            logo = base64.b64decode(nfe.company_id.logo)
        elif nfe.issuer != "company" and nfe.company_id.logo_web:
            logo = base64.b64decode(nfe.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False

        danfe_invoice_display = nfe.company_id.danfe_invoice_display
        config = self._get_danfe_config(tmpLogo, danfe_invoice_display)
        if nfe.company_id.danfe_display_pis_cofins:
            config.display_pis_cofins = True

        danfe = Danfe(xml=nfe_xml, config=config)

        tmpDanfe = BytesIO()
        danfe.output(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        return danfe_file, "pdf"

    def _get_danfe_config(self, tmpLogo, danfe_invoice_display):
        danfe_config = {
            "logo": tmpLogo,
            "margins": Margins(top=2, right=2, bottom=2, left=2),
        }

        if danfe_invoice_display == "duplicates_only":
            danfe_config["invoice_display"] = InvoiceDisplay.DUPLICATES_ONLY

        return DanfeConfig(**danfe_config)

    def render_danfe_erpbrasil(self, nfe_xml):
        pdf = base.ImprimirXml.imprimir(
            string_xml=nfe_xml,
        )
        return pdf, "pdf"
