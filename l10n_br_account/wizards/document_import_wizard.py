# Copyright 2023 Akretion (Raphaẽl Valyi <raphael.valyi@akretion.com.br>)
# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


def normalize_doc_number(value):
    """Drop leading zeros so 001 and 1 identify the same fiscal number."""
    text = (value or "").strip()
    if not text:
        return ""
    return text.lstrip("0") or "0"


class DocumentImportWizard(models.TransientModel):
    """
    Extend the generic Document Importer so that importing
    a fiscal document will also create an account move and so
    it can be used sequencially with several attachments from
    the vendor bills upload button.

    When a draft vendor bill already exists for the same supplier
    document, the XML completes that bill instead of creating another.
    """

    _inherit = "l10n_br_fiscal.document.import.wizard"

    # a transient wizard cannot be linked to any persistent
    # account.move record. So in case the user upload several
    # attachments, the solution we implemented
    # is to store the id of the 1st imported move and redirect
    # to the next imported account.move from there.
    first_imported_move_id = fields.Integer()

    candidate_move_ids = fields.Many2many(
        comodel_name="account.move",
        string="Candidate Vendor Bills",
    )
    target_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Vendor Bill to Complete",
        domain="[('id', 'in', candidate_move_ids)]",
    )
    create_new_move = fields.Boolean(
        string="Create a new vendor bill",
    )
    confirm_divergence = fields.Boolean(
        string="Confirm quantity and amount differences",
    )
    divergence_warning = fields.Text(readonly=True)
    match_line_ids = fields.One2many(
        comodel_name="l10n_br_account.document.import.match.line",
        inverse_name="wizard_id",
        string="Line Matching",
    )

    def _find_existing_document(self):
        """Reuse only an official imported document of this company."""
        key = (self.document_key or "").replace(" ", "")
        document = self.env["l10n_br_fiscal.document"]
        if key and self.company_id:
            document = document.search(
                [
                    ("document_key", "=", key),
                    ("company_id", "=", self.company_id.id),
                    ("imported_document", "=", True),
                ],
                limit=1,
            )
        self.document_id = document

    def _fill_wizard_from_binding(self):
        binding = super()._fill_wizard_from_binding()
        self._prepare_import_candidates()
        return binding

    def _issuer_partner_ids(self):
        partner = self.issuer_partner_id or self.partner_id
        if not partner:
            return []
        digits = punctuation_rm(partner.vat or "")
        if digits:
            partners = self.env["res.partner"].search(
                [("cnpj_cpf_stripped", "=", digits)]
            )
            if partners:
                return partners.ids
        commercial = partner.commercial_partner_id
        return (commercial | commercial.child_ids | partner).ids

    def _search_candidate_moves(self):
        """Draft vendor bills that may receive this XML."""
        moves = self.env["account.move"]
        if not self.company_id:
            return moves
        partner_ids = self._issuer_partner_ids()
        if partner_ids:
            domain = [
                ("move_type", "=", "in_invoice"),
                ("state", "=", "draft"),
                ("company_id", "=", self.company_id.id),
                ("partner_id", "in", partner_ids),
            ]
            if self.document_type_id:
                domain.append(("document_type_id", "=", self.document_type_id.id))
            moves = moves.search(domain)
        key = (self.document_key or "").replace(" ", "")
        if key:
            keyed = self.env["l10n_br_fiscal.document"].search(
                [
                    ("document_key", "=", key),
                    ("company_id", "=", self.company_id.id),
                ]
            )
            moves |= keyed.move_ids.filtered(
                lambda move: move.state == "draft" and move.move_type == "in_invoice"
            )
        return moves

    def _search_closed_moves(self):
        """Posted or cancelled bills that already use this document identity."""
        moves = self.env["account.move"]
        if not self.company_id:
            return moves
        partner_ids = self._issuer_partner_ids()
        number = normalize_doc_number(self.document_number)
        serie = normalize_doc_number(self.document_serie)
        if partner_ids and number:
            closed = self.env["account.move"].search(
                [
                    ("move_type", "=", "in_invoice"),
                    ("state", "!=", "draft"),
                    ("company_id", "=", self.company_id.id),
                    ("partner_id", "in", partner_ids),
                ]
            )
            if self.document_type_id:
                closed = closed.filtered(
                    lambda move: move.document_type_id == self.document_type_id
                )
            for move in closed:
                same_number = normalize_doc_number(move.document_number) == number
                same_serie = normalize_doc_number(move.document_serie) == serie
                if same_number and same_serie:
                    moves |= move
        key = (self.document_key or "").replace(" ", "")
        if key:
            keyed = self.env["l10n_br_fiscal.document"].search(
                [
                    ("document_key", "=", key),
                    ("company_id", "=", self.company_id.id),
                ]
            )
            moves |= keyed.move_ids.filtered(
                lambda move: move.state != "draft" and move.move_type == "in_invoice"
            )
        return moves

    def _is_strong_move_match(self, move):
        """Number and series identify the bill. Purchase orders extend this."""
        number = normalize_doc_number(self.document_number)
        serie = normalize_doc_number(self.document_serie)
        if not number:
            return False
        return (
            normalize_doc_number(move.document_number) == number
            and normalize_doc_number(move.document_serie) == serie
        )

    def _get_xml_line_previews(self):
        """Ordered preview of XML lines, before the fiscal document exists.

        NF-e and NFS-e wizards contribute their own lines when installed.
        """
        previews = []
        if "imported_products_ids" in self._fields and self.imported_products_ids:
            for sequence, line in enumerate(self.imported_products_ids):
                previews.append(
                    {
                        "sequence": sequence,
                        "name": line.product_name,
                        "product_id": line.product_id.id,
                        "quantity": line.quantity_com,
                        "price_unit": line.price_unit_com,
                        "partner_order": False,
                        "partner_order_line": False,
                    }
                )
            return previews
        product = self._fields.get("product_id") and self.product_id
        if product:
            previews.append(
                {
                    "sequence": 0,
                    "name": product.display_name,
                    "product_id": product.id,
                    "quantity": 1.0,
                    "price_unit": self.amount_total or 0.0,
                    "partner_order": False,
                    "partner_order_line": False,
                }
            )
        return previews

    def _prepare_import_candidates(self):
        candidates = self._search_candidate_moves()
        self.candidate_move_ids = candidates
        strong = candidates.filtered(lambda move: self._is_strong_move_match(move))
        if len(strong) == 1:
            self.target_move_id = strong
            self.create_new_move = False
        elif self.target_move_id not in candidates:
            self.target_move_id = False
        self._rebuild_match_lines()

    def _suggest_invoice_line(self, preview, invoice_lines, used_lines):
        """Return (invoice_line, ambiguous) for one XML preview."""
        available = invoice_lines - used_lines
        order = (preview.get("partner_order") or "").strip()
        item = (preview.get("partner_order_line") or "").strip()
        purchase_line_model = self.env.get("purchase.order.line")
        if (
            order
            and purchase_line_model is not None
            and "partner_order" in purchase_line_model._fields
            and "purchase_line_id" in available._fields
        ):
            by_order = available.filtered(
                lambda line, order=order, item=item: line.purchase_line_id
                and (line.purchase_line_id.partner_order or "").strip() == order
                and (
                    not item
                    or (line.purchase_line_id.partner_order_line or "").strip() == item
                )
            )
            if len(by_order) == 1:
                return by_order, False
            if len(by_order) > 1:
                return available.browse(), True
        product_id = preview.get("product_id")
        if product_id:
            by_product = available.filtered(
                lambda line: line.product_id.id == product_id
            )
            if len(by_product) == 1:
                return by_product, False
            if len(by_product) > 1:
                return available.browse(), True
        return available.browse(), False

    def _rebuild_match_lines(self):
        previews = self._get_xml_line_previews()
        invoice_lines = self.env["account.move.line"]
        if self.target_move_id and not self.create_new_move:
            invoice_lines = self.target_move_id._importable_invoice_lines()
        commands = [Command.clear()]
        used = self.env["account.move.line"]
        warnings = []
        for preview in previews:
            suggested, ambiguous = self._suggest_invoice_line(
                preview, invoice_lines, used
            )
            if suggested:
                used |= suggested
            elif ambiguous:
                warnings.append(
                    _(
                        "%(line)s can match more than one vendor bill line. "
                        "Choose the pair.",
                        line=preview.get("name") or preview.get("product_id"),
                    )
                )
            commands.append(
                Command.create(
                    {
                        "sequence": preview["sequence"],
                        "name": preview.get("name"),
                        "product_id": preview.get("product_id"),
                        "quantity": preview.get("quantity"),
                        "price_unit": preview.get("price_unit"),
                        "partner_order": preview.get("partner_order"),
                        "partner_order_line": preview.get("partner_order_line"),
                        "invoice_line_id": suggested.id,
                        "ambiguous": ambiguous,
                    }
                )
            )
        self.match_line_ids = commands
        self.divergence_warning = "\n".join(warnings) if warnings else False

    @api.onchange("target_move_id", "create_new_move")
    def _onchange_target_move_id(self):
        if self.file:
            self._rebuild_match_lines()

    def _raise_if_closed_identity(self):
        closed = self._search_closed_moves()
        if not closed:
            return
        move = closed[:1]
        raise UserError(
            _(
                "Vendor bill %(bill)s is %(state)s for this fiscal document "
                "and cannot receive the XML.",
                bill=move.display_name,
                state=move.state,
            )
        )

    def _draft_imported_move(self):
        self._find_existing_document()
        document = self.document_id
        if not document:
            return self.env["account.move"]
        return document.move_ids.filtered(
            lambda move: move.state == "draft" and move.move_type == "in_invoice"
        )[:1]

    def _candidate_choice_required(self):
        if self.create_new_move or self.target_move_id:
            return False
        candidates = self.candidate_move_ids or self._search_candidate_moves()
        return bool(candidates)

    def _release_shell_identity(self, shell):
        """Clear key and number that would block creating the official document."""
        if not shell:
            return
        vals = {}
        key = (self.document_key or "").replace(" ", "")
        shell_key = (shell.document_key or "").replace(" ", "")
        if key and shell_key == key:
            vals["document_key"] = False
        number = normalize_doc_number(self.document_number)
        serie = normalize_doc_number(self.document_serie)
        same_number = number and normalize_doc_number(shell.document_number) == number
        same_serie = normalize_doc_number(shell.document_serie) == serie
        if same_number and same_serie:
            vals["document_number"] = False
        if vals:
            shell.write(vals)

    def _line_map_for(self, fiscal_document):
        fiscal_lines = fiscal_document.fiscal_line_ids.sorted("id")
        match_lines = self.match_line_ids.sorted("sequence")
        line_map = {}
        for match_line, fiscal_line in zip(match_lines, fiscal_lines, strict=False):
            if match_line.invoice_line_id:
                line_map[fiscal_line.id] = match_line.invoice_line_id
        return line_map

    def _import_onto_existing_move(self):
        """Create the official document and apply it to the selected draft bill.

        Key and number of the shell are cleared in the same savepoint as the
        XML import. A failure restores that identity.
        """
        self.ensure_one()
        move = self.target_move_id
        if not move or move.state != "draft":
            raise UserError(_("Select a draft vendor bill to complete."))
        shell = move.fiscal_document_id
        with self.env.cr.savepoint():
            self._release_shell_identity(shell)
            self._find_existing_document()
            if self.document_id:
                document = self.document_id
            else:
                _binding, document = self._create_edoc_from_file()
                self.document_id = document
            if self.date_in_out and not document.date_in_out:
                document.date_in_out = self.date_in_out
            document._check_document_import()
            move._apply_imported_fiscal_document(
                document,
                confirm_divergence=self.confirm_divergence,
                line_map=self._line_map_for(document),
            )
        return document

    def _link_purchase_order_lines(self, move, fiscal_document):
        """Hook for l10n_br_purchase. Path A links the new bill to the PO."""
        return move

    def _action_open_move(self, move):
        return {
            "name": self.env._("Imported Invoice"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "form"]],
            "res_id": move.id,
            "res_model": "account.move",
        }

    def action_import_and_open_document(self):
        if self.target_move_id and not self.create_new_move:
            self._raise_if_closed_identity()
            self._import_onto_existing_move()
            return self.action_open_document()
        return super().action_import_and_open_document()

    def action_import_and_open_move(self):
        """
        Import the current file into a new vendor bill, or complete the
        draft bill selected on the wizard.
        """
        self._raise_if_closed_identity()
        existing = self._draft_imported_move()
        if existing:
            return self._finish_move_import(existing.id)

        if self.target_move_id and not self.create_new_move:
            self._import_onto_existing_move()
            return self._finish_move_import(self.target_move_id.id)

        if self._candidate_choice_required():
            raise UserError(
                _("Select the vendor bill to complete, or choose to create a new one.")
            )
        if self.create_new_move:
            self._raise_if_new_move_duplicates_shell()

        _binding, fiscal_document = self._import_edoc()
        fiscal_document._check_document_import()
        move_type = f"{self.fiscal_operation_type}_invoice"
        move_form = self.env["account.move"].import_fiscal_document(
            fiscal_document,
            move_type=move_type,
        )
        move = self.env["account.move"].browse(move_form.id)
        self._link_purchase_order_lines(move, fiscal_document)
        return self._finish_move_import(move.id)

    def _raise_if_new_move_duplicates_shell(self):
        key = (self.document_key or "").replace(" ", "")
        if not key:
            return
        shell = self.env["l10n_br_fiscal.document"].search(
            [
                ("document_key", "=", key),
                ("company_id", "=", self.company_id.id),
                ("imported_document", "=", False),
            ],
            limit=1,
        )
        bill = shell.move_ids.filtered(lambda move: move.state != "cancel")[:1]
        if bill:
            raise UserError(
                _(
                    "Access key %(key)s is already on vendor bill %(bill)s. "
                    "Complete that bill instead of creating a new one.",
                    key=key,
                    bill=bill.display_name,
                )
            )

    def _finish_move_import(self, move_id):
        attachments = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "l10n_br_fiscal.document.import.wizard"),
                    ("res_id", "=", self.id),
                    ("create_uid", "=", self._uid),
                ],
                order="id",
            )
        )
        if attachments:
            attachments[0].res_model = "account.move"
            attachments[0].res_id = move_id

        if len(attachments) > 1:
            return self._get_importer_action(attachments[1:], move_id=move_id)
        if not self.first_imported_move_id:
            return self._action_open_move(self.env["account.move"].browse(move_id))
        moves = self.env["account.move"].search(
            [
                ("imported_document", "=", True),
                ("id", ">=", self.first_imported_move_id),
                ("create_uid", "=", self._uid),
            ]
        )
        return {
            "name": self.env._("Imported Invoices"),
            "type": "ir.actions.act_window",
            "target": "current",
            "views": [[False, "tree"], [False, "form"]],
            "res_ids": moves.ids,
            "res_model": "account.move",
        }

    def _get_importer_action(self, attachments, move_id=None):
        """
        Try to parse the 1st file of the the attachments to
        detect its type and return the wizard import action.
        Also mark the other attachments to be imported next.
        """
        wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
            {
                "file": attachments[0].datas,
                "first_imported_move_id": self.first_imported_move_id or move_id,
            }
        )

        for attachment in attachments:
            attachment.res_model = "l10n_br_fiscal.document.import.wizard"
            attachment.res_id = wizard.id

        wizard._onchange_file()
        return {
            "name": self.env._("Adjust Importation"),
            "type": "ir.actions.act_window",
            "target": "new",
            "views": [[False, "form"]],
            "res_id": wizard.id,
            "res_model": "l10n_br_fiscal.document.import.wizard",
        }
