# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import re
from collections import defaultdict, deque

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Width of the order reference the matching key is built on. The fiscal field
# was a Char(15) - the NF-e layout cap for xPed - but a buyer reference is not
# only the NF-e spelling: the purchase order of a customer may be named with a
# prefix of its own ("J-MT/OC/26/40795", 16 characters), and truncating it makes
# every order of the same decade share the key ("J-MT/OC/26/4079" for 40790 to
# 40799), i.e. two receipts become interchangeable. The bill matching only needs
# the two sides to agree, so the field is widened and the reference is kept
# whole; see the pre-migrate scripts of l10n_br_fiscal, l10n_br_account,
# l10n_br_stock_account and l10n_br_contract for the existing tables.
PARTNER_ORDER_SIZE = 32
PARTNER_ORDER_LINE_SIZE = 6


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

    @staticmethod
    def _normalize_order_ref(reference):
        """Digits of a buyer order reference, punctuation and prefix dropped.

        Anything that is not a text value counts as "no reference": the field
        is optional, and a caller (or a test double) may hand over something
        that is not a string at all. Raising there would turn a missing
        reference into a crash of the whole import.
        """
        if not isinstance(reference, str):
            return ""
        return re.sub(r"\D", "", reference)

    def _search_orders_by_reference(self, xped):
        """Purchase orders of the issuer the reference ``xped`` designates.

        The exact spellings come first: suppliers usually echo either
        ``purchase.order.name`` or the ``partner_ref`` the buyer filled. They
        are not the only ones seen in practice though - the same order is
        printed as ``26/40795`` (the buyer prefix dropped), ``40900`` (the
        sequence alone), ``JMTOC2640979`` (separators dropped) or ``2640884``
        (year and sequence only) - so the reference is compared on its digits
        when the exact search found nothing, keeping the orders whose name or
        partner reference ends with those digits.

        The caller still requires a UNIQUE order carrying the XML item, so a
        loose spelling never decides on its own: it narrows the list, and an
        ambiguous result leaves the match source empty for the operator.
        """
        order_model = self.env["purchase.order"].sudo()
        if not isinstance(xped, str) or not xped.strip():
            # nothing to compare: an empty xPed, or a value that is not text
            return order_model.browse()
        company = self.company_id or self.env.company
        base_domain = [
            ("partner_id", "=", self.issuer_partner_id.id),
            ("company_id", "=", company.id),
        ]
        orders = order_model.search(
            base_domain + ["|", ("name", "=", xped), ("partner_ref", "=", xped)]
        )
        if orders:
            return orders
        digits = self._normalize_order_ref(xped)
        if not digits:
            return order_model.browse()
        # the trailing sequence identifies the order in every spelling; asking
        # SQL for it keeps the search bounded instead of walking every order of
        # the supplier
        digits_tail = digits[-5:]
        candidates = order_model.search(base_domain + [("name", "ilike", digits_tail)])
        return candidates.filtered(
            lambda order: self._normalize_order_ref(order.name).endswith(digits)
            or self._normalize_order_ref(order.partner_ref).endswith(digits)
        )

    def _match_po_line(self, xml_product):
        """Return the purchase.order.line referenced by the XML hints.

        On an inbound document, ``xPed`` holds the buyer's purchase order
        reference and ``nItemPed`` the 1-based item position inside that
        order. ``xPed`` is resolved by ``_search_orders_by_reference``: the
        exact ``purchase.order.name`` / ``partner_ref`` first, then the
        spellings suppliers actually print (prefix dropped, separators
        dropped, sequence alone). ``nItemPed`` is matched by
        POSITION: ``purchase.order.line.sequence`` defaults to 10 for every
        line created in the interface, so it cannot be used; the accountable
        lines come ordered by ``sequence, id`` (sections and notes excluded,
        they are not items), so the n-th item is ``lines[nItemPed - 1]``.

        Soft dependency: returns ``None`` when ``purchase`` is not installed,
        an empty recordset when no line matches.
        """
        pol_model = self.env.get("purchase.order.line")
        if pol_model is None:
            return None
        xped = (getattr(xml_product, "xPed", "") or "").strip()
        if not xped:
            return pol_model.browse()

        orders = self._search_orders_by_reference(xped)
        if not orders:
            return pol_model.browse()
        if len(orders) > 1:
            # xPed is ambiguous: the same reference on several orders (a
            # supplier reusing the buyer reference, or a vendor reference
            # shared by two orders). Keep only the orders actually carrying
            # the XML item and require exactly one, otherwise leave the match
            # source empty for the operator to decide.
            orders = orders.filtered(
                lambda order: self._order_has_xml_item(order, xml_product)
            )
            if len(orders) != 1:
                return pol_model.browse()
        order = orders

        # Only the accountable lines are items of the document: a section or a
        # note must not consume a position, otherwise every nItemPed after it
        # designates the wrong line (and the same expression is used on the
        # receipt side, so both sides would agree on the wrong line — see
        # PO_LINE_POSITION_SQL in document_import_match_candidate).
        lines = order.order_line.filtered(lambda line: not line.display_type)
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

    def _order_has_xml_item(self, order, xml_product):
        """True when the order carries a line matching the XML item.

        Used to disambiguate a duplicated ``xPed`` (see ``_match_po_line``):
        the product code (``cProd``) or the barcode (``cEANTrib``) tells which
        order the XML line actually refers to. No blanket fallback here: when
        no competing order can be told apart, the caller leaves the match
        source empty for the operator instead of guessing.
        """
        cprod = getattr(xml_product, "cProd", None)
        ean = getattr(xml_product, "cEANTrib", None)
        for line in order.order_line.filtered(lambda line: not line.display_type):
            if cprod and line.product_id.default_code == cprod:
                return True
            if ean and ean != "SEM GTIN" and line.product_id.barcode == ean:
                return True
        return False

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

        Document lines without a selected match source are left untouched; a
        line whose document carried its own xPed / nItemPed but which the
        operator pointed at another order line gets the operator's reference and
        a warning in the log — the wizard already shows the contradiction on the
        line (see ``match_source_conflict``), so it never happens in silence.
        """
        # NB: a product may legitimately appear on several XML lines (the
        # supplier splitting his own invoice, or shipping the same product
        # twice). A product-keyed dict would keep only the LAST wizard line
        # and stamp the same source on every fiscal line of that product, so
        # the wizard lines are consumed in ORDER instead: the XML lines and
        # the fiscal lines are built in the same order, hence the n-th fiscal
        # line of a product pairs with the n-th wizard line of that product.
        wizard_lines = self.imported_products_ids
        if not wizard_lines.filtered("match_source_id"):
            return
        by_product = defaultdict(deque)
        by_code = defaultdict(deque)
        for wizard_line in wizard_lines:
            if wizard_line.product_id:
                by_product[wizard_line.product_id.id].append(wizard_line)
            if wizard_line.product_code:
                by_code[wizard_line.product_code].append(wizard_line)
        consumed = set()

        def _pop(queue):
            """Next not-yet-consumed wizard line of a product queue."""
            while queue:
                candidate = queue.popleft()
                if candidate.id not in consumed:
                    consumed.add(candidate.id)
                    return candidate
            return None

        for line in edoc.fiscal_line_ids:
            wizard_line = None
            if line.product_id:
                wizard_line = _pop(by_product[line.product_id.id])
                if not wizard_line:
                    wizard_line = _pop(by_code[line.product_id.default_code])
            if not wizard_line or not wizard_line.match_source_id:
                continue
            source = wizard_line.match_source_id
            if source.source_type == "po_line":
                reference = (source.ref_name, str(source.line_no))
            elif source.po_ref:
                # move linked to a PO line: use the canonical PO key
                reference = (source.po_ref, str(source.po_line_no))
            else:
                continue
            if (line.partner_order, line.partner_order_line) not in (
                (False, False),
                ("", ""),
                reference,
            ):
                # The document carried its own xPed/nItemPed and the operator
                # picked another order line: the pick wins (it is the explicit
                # decision, and the wizard flags the contradiction on the line
                # as match_source_conflict), but it must not happen in silence.
                _logger.warning(
                    "bill matching reference of %s overwritten by the operator: "
                    "the document says %s item %s, the match source says %s item %s",
                    edoc.document_key or edoc.document_number,
                    line.partner_order,
                    line.partner_order_line,
                    *reference,
                )
            line.partner_order = reference[0][:PARTNER_ORDER_SIZE]
            line.partner_order_line = reference[1][:PARTNER_ORDER_LINE_SIZE]
