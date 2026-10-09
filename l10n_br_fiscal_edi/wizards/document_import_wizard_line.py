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

    match_source_product_matched = fields.Boolean(
        compute="_compute_match_source_product_matched",
        help="True when the issuer has at least one open purchase order line "
        "or pending incoming picking move for this line's product. False "
        "means there is nothing to match the line against (the imported bill "
        "will not be reconcilable with a receipt for it).",
    )

    @api.depends("product_id", "issuer_partner_id", "company_id")
    def _compute_match_source_product_matched(self):
        candidate_model = self.env[
            "l10n_br_fiscal.document.import.match.candidate"
        ].sudo()
        # the candidate model is a raw SQL view: flush pending ORM writes
        # (the line's product may just have been set by the operator or by
        # the auto-preselection) before querying it.
        self.env.flush_all()
        matched_by_key = {}
        for line in self:
            if not line.product_id or not line.issuer_partner_id:
                line.match_source_product_matched = False
                continue
            key = (line.issuer_partner_id.id, line.company_id.id)
            if key not in matched_by_key:
                matched_by_key[key] = set(
                    candidate_model.search(
                        [
                            ("partner_id", "=", key[0]),
                            ("company_id", "=", key[1]),
                        ]
                    ).mapped("product_id.id")
                )
            line.match_source_product_matched = (
                line.product_id.id in matched_by_key[key]
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
