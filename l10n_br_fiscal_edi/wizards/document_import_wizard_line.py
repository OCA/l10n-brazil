# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class DocumentImportWizardLine(models.TransientModel):
    """Generic match-source fields for the fiscal document import wizard
    line. Each specialized importer (NFe, CTe, NFSe...) inherits the
    generic line and surfaces match_source_id in its own tree view."""

    _inherit = "l10n_br_fiscal.document.import.wizard.line"

    match_source_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.import.match.candidate",
        string="Match Source",
        help="Pre-existing purchase order line or incoming picking move this "
        "XML line corresponds to. Selecting it sets the product and the "
        "internal UoM automatically and ties the imported document to the "
        "referenced order/receipt.",
    )

    company_id = fields.Many2one(related="import_xml_id.company_id")

    issuer_partner_id = fields.Many2one(related="import_xml_id.issuer_partner_id")

    match_source_available = fields.Boolean(
        related="import_xml_id.match_source_available"
    )

    @api.onchange("match_source_id")
    def _onchange_match_source_id(self):
        for line in self:
            if line.match_source_id:
                line.product_id = line.match_source_id.product_id
                if line.match_source_id.uom_id:
                    line.uom_internal = line.match_source_id.uom_id

    @api.onchange("product_id")
    def _onchange_product_id_match_source(self):
        for line in self:
            if (
                line.match_source_id
                and line.match_source_id.product_id != line.product_id
            ):
                line.match_source_id = False
