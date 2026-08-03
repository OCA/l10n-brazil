# Copyright 2024 Engenere.one
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.damdfe import Damdfe, DamdfeConfig, Margins
from lxml import etree

from odoo import _, api, models
from odoo.exceptions import UserError

MDFE_NS = "http://www.portalfiscal.inf.br/mdfe"


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, res_ids, data=None):
        if report_ref == "main_template_damdfe":
            return
        return super()._render_qweb_html(report_ref, res_ids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids, data=None):
        if report_ref not in ["main_template_damdfe"]:
            return super()._render_qweb_pdf(report_ref, res_ids, data=data)

        mdfe = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])

        return self._render_damdfe(mdfe)

    def _render_damdfe(self, mdfe):
        if mdfe.document_type != "58":
            raise UserError(_("You can only print a DAMDFE of a MDFe(58)."))

        mdfe_xml = False
        if mdfe.authorization_file_id:
            mdfe_xml = base64.b64decode(mdfe.authorization_file_id.datas)
        elif mdfe.send_file_id:
            mdfe_xml = base64.b64decode(mdfe.send_file_id.datas)

        if not mdfe_xml:
            raise UserError(_("No xml file was found."))

        mdfe_xml = self._update_damdfe_tot(mdfe, mdfe_xml)

        return self.render_damdfe_brazilfiscalreport(mdfe, mdfe_xml)

    def _update_damdfe_tot(self, mdfe, mdfe_xml):
        """Update the ``tot`` values of the stored XML with the current
        document values before rendering the DAmDFE.

        The stored XML may have been generated before the weight/amount
        sync, so the ``qCarga``/``vCarga`` totals must be refreshed from
        the document to render the correct "PESO TOTAL" and
        "VALOR TOTAL" on the DAmDFE.
        """
        root = etree.fromstring(mdfe_xml)
        tot = root.find(f".//{{{MDFE_NS}}}tot")
        if tot is None:
            return mdfe_xml

        values = {
            "qNFe": mdfe.mdfe30_qNFe or 0,
            "qCTe": mdfe.mdfe30_qCTe or 0,
            "qMDFe": mdfe.mdfe30_qMDFe or 0,
            "vCarga": f"{mdfe.mdfe30_vCarga:.2f}",
            # The library prints the qCarga text as-is, so format the
            # weight with a comma decimal separator and 2 digits.
            "qCarga": f"{mdfe.mdfe30_qCarga or 0:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", "."),
        }
        for tag, value in values.items():
            element = tot.find(f"{{{MDFE_NS}}}{tag}")
            if element is not None:
                if element.text != str(value):
                    element.text = str(value)
            elif tag in ("vCarga", "qCarga"):
                # mandatory tot fields missing on old XMLs: append them
                etree.SubElement(tot, f"{{{MDFE_NS}}}{tag}").text = str(value)

        return etree.tostring(root, encoding="UTF-8")

    def render_damdfe_brazilfiscalreport(self, mdfe, mdfe_xml):
        logo = False
        if mdfe.issuer == "company" and mdfe.company_id.logo:
            logo = base64.b64decode(mdfe.company_id.logo)
        elif mdfe.issuer != "company" and mdfe.company_id.logo_web:
            logo = base64.b64decode(mdfe.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False
        config = self._get_damdfe_config(tmpLogo, mdfe.company_id)

        damdfe = Damdfe(xml=mdfe_xml, config=config)

        tmpDamdfe = BytesIO()
        damdfe.output(tmpDamdfe)
        damdfe_file = tmpDamdfe.getvalue()
        tmpDamdfe.close()

        return damdfe_file, "pdf"

    @api.model
    def _get_damdfe_config(self, tmpLogo, company):
        margins = Margins(
            top=company.damdfe_margin_top,
            right=company.damdfe_margin_right,
            bottom=company.damdfe_margin_bottom,
            left=company.damdfe_margin_left,
        )
        damdfe_config = {
            "logo": tmpLogo,
            "margins": margins,
        }
        return DamdfeConfig(**damdfe_config)
