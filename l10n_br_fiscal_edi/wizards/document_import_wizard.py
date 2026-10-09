# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DocumentImportWizard(models.TransientModel):
    """Generic match-source support for the fiscal document import wizard.

    Lives in l10n_br_fiscal_edi so every document importer (NFe, CTe, NFSe,
    future utility-bill importers...) inherits it through the generic
    wizard. The candidate view (l10n_br_fiscal.document.import.match.
    candidate) is document-agnostic: open purchase order lines and pending
    incoming picking moves of the issuer. Services documents (NFSe) simply
    see no picking candidates.

    Each specialized wizard surfaces the fields in its own tree view (Odoo
    tree views cannot be extended generically) and may override the
    ``_match_import_candidate`` hints extraction from its own binding.
    """

    _inherit = "l10n_br_fiscal.document.import.wizard"

    match_source_available = fields.Boolean(
        compute="_compute_match_source_available",
        help="True when the document issuer has open purchase order lines or "
        "pending incoming picking moves the imported lines can be matched "
        "against (requires the purchase and/or stock modules).",
    )

    @api.depends("issuer_partner_id", "company_id")
    def _compute_match_source_available(self):
        for wizard in self:
            if not wizard.issuer_partner_id:
                wizard.match_source_available = False
                continue
            wizard.match_source_available = bool(
                wizard.env["l10n_br_fiscal.document.import.match.candidate"]
                .sudo()
                .search_count(
                    [
                        ("partner_id", "=", wizard.issuer_partner_id.id),
                        (
                            "company_id",
                            "=",
                            (wizard.company_id or wizard.env.company).id,
                        ),
                    ],
                    limit=1,
                )
            )

    def _import_edoc(self):
        res = super()._import_edoc()
        # carried into the generic flow so every document importer gets the
        # match-source reference write-back for free
        self._propagate_match_source_to_document(self.document_id)
        return res

    def _match_import_candidate(self, xml_product, product_id):
        """Preselect the match source (open PO line or pending incoming
        picking move) for an imported product line.

        Priority:
        1. the purchase order line referenced by the XML hints (xPed /
           nItemPed semantics: (partner order ref, 1-based line position));
        2. when the product is matched and exactly one LOGICAL candidate
           exists for the (issuer, product) pair — a PO line and its own
           receipt move (move.purchase_line_id) count as one, with the move
           preferred since the bill matching reconciles against pickings;
        3. otherwise nothing: the operator picks from the dropdown.

        ``xml_product`` is the per-line binding object of the specialized
        importer. The NFe layout hints are read through duck-typed
        attribute access, so other document layouts are free to pass any
        object; a simple namespace with the keys below (or an empty
        MagicMock-like stub) works too:
          - xPed / nItemPed: the buyer's PO reference and 1-based line
            position (optional, matched against purchase.order.name /
            partner_ref and the line position);
          - cProd / cEANTrib: fallback product disambiguation keys.
        """
        candidate_model = self.env[
            "l10n_br_fiscal.document.import.match.candidate"
        ].sudo()
        # the candidate model is a raw SQL view: it cannot see records the
        # current transaction only has in the ORM cache (e.g. a PO created
        # right before parsing in the tests) — flush first.
        self.env.flush_all()

        po_line = self._match_po_line(xml_product)
        if po_line:
            candidate = candidate_model.search(
                [("source_type", "=", "po_line"), ("id", "=", po_line.id)]
            )
            if candidate:
                return candidate
        if not product_id:
            return candidate_model.browse()
        candidates = candidate_model.search(
            [
                ("partner_id", "=", self.issuer_partner_id.id),
                ("company_id", "=", (self.company_id or self.env.company).id),
                ("product_id", "=", product_id.id),
            ]
        )
        return self._collapse_candidates(candidates)

    def _match_po_line(self, xml_product):
        """Return the purchase.order.line referenced by the XML hints.

        On an inbound document, ``xPed`` holds the buyer's purchase order
        reference and ``nItemPed`` the 1-based item position inside that
        order. ``xPed`` is matched against both ``purchase.order.name`` (the
        supplier echoes the buyer's PO number) and
        ``purchase.order.partner_ref`` (the vendor reference the buyer fills
        precisely to match incoming goods). ``nItemPed`` is matched by
        POSITION: ``purchase.order.line.sequence`` defaults to 10 for every
        line created in the interface, so it cannot be used; the order lines
        come ordered by ``sequence, id``, so the n-th line is
        ``order.order_line[nItemPed - 1]``.

        Soft dependency: returns ``None`` when ``purchase`` is not installed,
        an empty recordset when no line matches.
        """
        pol_model = self.env.get("purchase.order.line")
        if pol_model is None:
            return None
        xped = (getattr(xml_product, "xPed", "") or "").strip()
        if not xped:
            return pol_model.browse()

        company = self.company_id or self.env.company
        order = (
            self.env["purchase.order"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", self.issuer_partner_id.id),
                    ("company_id", "=", company.id),
                    "|",
                    ("name", "=", xped),
                    ("partner_ref", "=", xped),
                ],
                limit=1,
            )
        )
        if not order:
            return pol_model.browse()

        lines = order.order_line
        nitemped = (getattr(xml_product, "nItemPed", "") or "").strip()
        if nitemped:
            try:
                position = int(nitemped)
            except ValueError:
                position = None
            if position is not None and 1 <= position <= len(lines):
                return lines[position - 1]

        # heuristic fallback: disambiguate the referenced order's line by the
        # XML product code / barcode when nItemPed is missing or out of range.
        if len(lines) == 1:
            return lines
        cprod = getattr(xml_product, "cProd", None)
        ean = getattr(xml_product, "cEANTrib", None)
        for line in lines:
            if cprod and line.product_id.default_code == cprod:
                return line
            if ean and ean != "SEM GTIN" and line.product_id.barcode == ean:
                return line
        return pol_model.browse()

    def _collapse_candidates(self, candidates):
        """Collapse to one LOGICAL candidate and return it when unique.

        Without this, confirming a PO with purchase_stock installed always
        yields two rows (the PO line and its move) for what is commercially
        one line, defeating the unique-candidate auto-preselection:
        - a PO line and its own receipt move(s) count as one candidate, with
          the move preferred (the bill matching reconciles against pickings);
        - several moves of the SAME PO line (one PO received over several
          pickings) also collapse: their canonical bill-matching key
          (PO name + line position) is identical, so any of them will do;
        - unlinked moves (pickings with no PO, e.g. "simples remessa") stay
          distinct.
        """
        moves = candidates.filtered(lambda c: c.source_type == "stock_move")
        po_lines = candidates - moves
        linked_pol_ids = set(moves.mapped("po_line_id"))
        standalone = po_lines.filtered(lambda c: c.id not in linked_pol_ids)
        move_representatives = {}
        for move in moves:
            key = move.po_line_id or ("move", -move.id)
            move_representatives.setdefault(key, move)
        effective = standalone | self.env[
            "l10n_br_fiscal.document.import.match.candidate"
        ].browse([m.id for m in move_representatives.values()])
        if len(effective) == 1:
            return effective
        return candidates.browse()

    def _propagate_match_source_to_document(self, edoc):
        """Carry the wizard's match sources onto the fiscal document lines as
        the canonical (partner_order, partner_order_line) = (PO name, 1-based
        line position) key.

        Those keys are optional in most document layouts, so most supplier
        XMLs carry nothing. When the operator (or the auto-preselection)
        picked a match source, the import synthesizes the key the supplier
        didn't send: it lands on the fiscal line (l10n_br_fiscal.document.
        line.mixin fields, available on every document type), flows to the
        stored related fields on account.move.line (l10n_br_account) and
        lets stock_picking_bill_matching reconcile the bill against the
        receipt with no hard dependency between the modules. Service
        documents (NFSe) and others without stock matching keep the
        reference as navigation/tracing metadata.

        Document lines without a selected match source are left untouched.
        """
        wizard_lines = self.imported_products_ids.filtered("match_source_id")
        if not wizard_lines:
            return
        by_product = {w.product_id.id: w for w in wizard_lines if w.product_id}
        by_code = {w.product_code: w for w in wizard_lines if w.product_code}
        for line in edoc.fiscal_line_ids:
            wizard_line = by_product.get(line.product_id.id) or (
                line.product_id and by_code.get(line.product_id.default_code)
            )
            if not wizard_line:
                continue
            source = wizard_line.match_source_id
            if source.source_type == "po_line":
                line.partner_order = source.ref_name[:15]
                line.partner_order_line = str(source.line_no)[:6]
            elif source.po_ref:
                # move linked to a PO line: use the canonical PO key
                line.partner_order = source.po_ref[:15]
                line.partner_order_line = str(source.po_line_no)[:6]
