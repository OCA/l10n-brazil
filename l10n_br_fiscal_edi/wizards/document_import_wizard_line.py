# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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

    document_partner_order = fields.Char(
        string="Document Order Ref.",
        help="Buyer purchase order reference carried by the document itself "
        "(xPed in an NF-e). It is the supplier's own statement: the wizard "
        "preselects the match source from it and keeps it on the imported "
        "document, so a source that points elsewhere is refused instead of "
        "silently replacing it.",
    )

    document_partner_order_line = fields.Char(string="Document Order Line")

    match_source_conflict = fields.Boolean(
        compute="_compute_match_source_conflict",
        help="The selected match source designates another order line than the "
        "one the document itself refers to.",
    )

    @api.depends(
        "match_source_id", "document_partner_order", "document_partner_order_line"
    )
    def _compute_match_source_conflict(self):
        for line in self:
            line.match_source_conflict = bool(line._match_source_mismatch())

    def _source_reference(self):
        """Canonical (order, position) key of the selected match source."""
        self.ensure_one()
        source = self.match_source_id
        if not source:
            return None
        if source.source_type == "po_line":
            return (source.ref_name, str(source.line_no))
        if source.po_ref:
            return (source.po_ref, str(source.po_line_no))
        return (source.ref_name, str(source.line_no))

    def _match_source_mismatch(self):
        """The selected source and the document disagree on the order line.

        Only a document that carries its own reference can disagree;
        ``partner_order_line`` may legitimately be missing from the XML while
        the order is not, so the comparison is on the order first and on the
        position only when the document states one.
        """
        self.ensure_one()
        if not self.match_source_id or not self.document_partner_order:
            return False
        order, position = self._source_reference()
        order_digits = re.sub(r"\D", "", order or "")
        document_digits = re.sub(r"\D", "", self.document_partner_order or "")
        if not order_digits or not document_digits:
            return False
        if not (
            order_digits.endswith(document_digits)
            or document_digits.endswith(order_digits)
        ):
            return True
        document_line = (self.document_partner_order_line or "").strip()
        return bool(document_line) and document_line != str(position).strip()

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

    @api.constrains("match_source_id", "product_id", "company_id")
    def _check_match_source_id(self):
        """Server-side guard on the selected match source.

        The m2o domain only filters the dropdown: a source written through
        RPC, an import or a crafted call must still belong to the wizard's
        company and issuer, and stay coherent with the line product — the
        reference synthesized at import time steers the bill matching, so a
        wrong source would silently reconcile the bill against the wrong
        document.
        """
        for line in self:
            source = line.match_source_id
            if not source:
                continue
            company = line.company_id or line.env.company
            if source.company_id != company:
                raise ValidationError(
                    _(
                        "The match source %(ref)s belongs to another company "
                        "than the imported document.",
                        ref=source.display_name,
                    )
                )
            if line.issuer_partner_id and source.partner_id != line.issuer_partner_id:
                raise ValidationError(
                    _(
                        "The match source %(ref)s belongs to another supplier "
                        "than the imported document.",
                        ref=source.display_name,
                    )
                )
            if line.product_id and source.product_id != line.product_id:
                raise ValidationError(
                    _(
                        "The match source %(ref)s is not for the line's "
                        "product %(product_name)s.",
                        ref=source.display_name,
                        product_name=line.product_id.display_name,
                    )
                )
            if line._match_source_mismatch():
                # Not refused: the operator may know better than the document
                # (a supplier reusing a stale reference), and the PR keeps the
                # explicit pick authoritative. The flag is what stops it from
                # being silent - the wizard tree paints the line red and shows
                # the reference the document itself carries.
                _logger.warning(
                    "match source %s disagrees with the reference printed on "
                    "the document (%s item %s)",
                    source.display_name,
                    line.document_partner_order,
                    line.document_partner_order_line or "?",
                )
