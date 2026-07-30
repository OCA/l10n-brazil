# Copyright (C) 2023 Antônio S. P. Neto <neto@engene.one> - Engenere LTDA
#     (https://engenere.one).
# Copyright (C) 2023 Marcel Savegnago <marcel.savegnago@escodoo.com.br> - Escodoo
#     (https://www.escodoo.com.br).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_NFSE
from odoo.addons.l10n_br_nfse_paulistana.models.document import filter_paulistana

NFSE_PRINT_URL = "https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx"


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    url_nfse_paulistana = fields.Char(
        string="URL of NFSe Paulistana",
        compute="_compute_url_nfse_paulistana",
        help="URL to access the Nota Fiscal de Serviços Eletrônicos (NFSe) "
        "from the São Paulo City (Paulistana).",
    )

    is_nfse_paulistana = fields.Boolean(
        string="Is NFSe Paulistana?",
        compute="_compute_is_nfse_paulistana",
        help="Technical field to identify if the document is a NFSe Paulistana.",
    )

    @api.depends(
        "document_number",
        "verify_code",
        "company_id.partner_id.l10n_br_im_code",
    )
    def _compute_url_nfse_paulistana(self):
        for doc in self:
            inscricao = doc.company_id.partner_id.l10n_br_im_code
            # The three values make up the URL: without any of them the city
            # hall returns an error, so we rather not offer the link at all.
            if not all([doc.document_number, inscricao, doc.verify_code]):
                doc.url_nfse_paulistana = ""
                continue
            doc.url_nfse_paulistana = (
                f"{NFSE_PRINT_URL}?nf={doc.document_number}"
                f"&inscricao={inscricao}&verificacao={doc.verify_code}"
            )

    @api.depends("document_type_id", "company_id.provedor_nfse")
    def _compute_is_nfse_paulistana(self):
        for doc in self:
            doc.is_nfse_paulistana = bool(
                doc.document_type_id.code == MODELO_FISCAL_NFSE
                and filter_paulistana(doc)
            )

    def action_open_nfse_paulistana(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.url_nfse_paulistana,
            "target": "new",
        }
