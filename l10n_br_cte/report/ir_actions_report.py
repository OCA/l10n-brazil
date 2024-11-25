# Copyright 2024 Engenere.one
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO

from brazilfiscalreport.dacte import Dacte, DacteConfig, Margins

from odoo import _, api, models
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, res_ids, data=None):
        if self.report_name == "main_template_dacte":
            return

        return super()._render_qweb_html(res_ids, data=data)

    def _render_qweb_pdf(self, res_ids, data=None):
        if self.report_name not in ["main_template_dacte"]:
            return super()._render_qweb_pdf(res_ids, data=data)

        cte = self.env["l10n_br_fiscal.document"].search([("id", "in", res_ids)])

        return self._render_dacte(cte)

    def _render_dacte(self, cte):
        if cte.document_type != "57":
            raise UserError(_("You can only print a DACTE of a CTe(57)."))

        cte_xml = False
        if cte.authorization_file_id:
            cte_xml = base64.b64decode(cte.authorization_file_id.datas)
        elif cte.send_file_id:
            cte_xml = base64.b64decode(cte.send_file_id.datas)

        if not cte_xml:
            raise UserError(_("No xml file was found."))

        return self.render_dacte_brazilfiscalreport(cte, cte_xml)

    def render_dacte_brazilfiscalreport(self, cte, cte_xml):
        logo = False
        if cte.issuer == "company" and cte.company_id.logo:
            logo = base64.b64decode(cte.company_id.logo)
        elif cte.issuer != "company" and cte.company_id.logo_web:
            logo = base64.b64decode(cte.company_id.logo_web)

        if logo:
            tmpLogo = BytesIO()
            tmpLogo.write(logo)
            tmpLogo.seek(0)
        else:
            tmpLogo = False
        config = self._get_dacte_config(tmpLogo, cte.company_id)

        dacte = Dacte(xml=cte_xml, config=config)

        tmpDacte = BytesIO()
        dacte.output(tmpDacte)
        dacte_file = tmpDacte.getvalue()
        tmpDacte.close()

        return dacte_file, "pdf"

    @api.model
    def _get_dacte_config(self, tmpLogo, company):
        margins = Margins(
            top=company.dacte_margin_top,
            right=company.dacte_margin_right,
            bottom=company.dacte_margin_bottom,
            left=company.dacte_margin_left,
        )
        dacte_config = {
            "logo": tmpLogo,
            "margins": margins,
        }
        return DacteConfig(**dacte_config)
