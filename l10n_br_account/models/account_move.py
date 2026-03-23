# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


import logging
from contextlib import contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo.tools import frozendict

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_IN_OUT_ALL,
    FISCAL_OUT,
    MODELO_FISCAL_NFE,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_EM_DIGITACAO,
)

from .constants import (
    MOVE_TO_OPERATION,
)

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = "account.move"
    _fiscal_decorator_model = "l10n_br_fiscal.document"
    _inherit = [
        _name,
        "l10n_br_account.decorator.mixin",
    ]

    # an account.move has normally 0 or 1 related fiscal document:
    # - 0 when it is not related to a Brazilian company for instance.
    # - 1 otherwise (usually). In this case the _inherits system
    # makes it easy to edit all the fiscal document (lines) fields
    # through the account.move form.
    # in some rare cases an account.move may have several fiscal
    # documents (1 on each account.move.line). In this case
    # fiscal_document_id might be used only to sync the "main" fiscal
    # document (or the one currently imported or edited). In this case,
    # fiscal_document_ids contains all the line fiscal documents.
    _inherits = {_fiscal_decorator_model: "fiscal_document_id"}

    _order = "date DESC, name DESC"

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
    )

    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        copy=False,
        ondelete="cascade",
        store=True,
        readonly=False,
    )

    fiscal_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Documents",
        compute="_compute_fiscal_document_ids",
        help="""In some rare cases (NFS-e, CT-e...) a single account.move
        may have several different fiscal documents related to its account.move.lines.
        """,
    )

    fiscal_operation_type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        related=None,
        compute="_compute_fiscal_operation_type",
    )

    @api.onchange("partner_id")
    def _inverse_partner_id(self):
        for move in self:
            move.proxy_partner_id = move.partner_id

    @api.onchange("partner_shipping_id")
    def _inverse_partner_shipping_id(self):
        for move in self:
            move.proxy_partner_shipping_id = move.partner_shipping_id

    @api.onchange("company_id")
    def _inverse_company_id(self):
        for move in self:
            move.proxy_company_id = move.company_id

    # account.move.user_id is a related field pointing to invoice_user_id,
    # so it may not be present in create/write vals. We sync from
    # invoice_user_id directly to ensure proxy_user_id gets the value.
    @api.onchange("invoice_user_id")
    def _inverse_user_id(self):
        for move in self:
            move.proxy_user_id = move.invoice_user_id

    @api.model
    def _sync_proxy_fields_vals(self, vals):
        if "proxy_partner_id" not in vals and "partner_id" in vals:
            vals["proxy_partner_id"] = vals["partner_id"]
        if "proxy_partner_shipping_id" not in vals and "partner_shipping_id" in vals:
            vals["proxy_partner_shipping_id"] = vals["partner_shipping_id"]
        if "proxy_company_id" not in vals and "company_id" in vals:
            vals["proxy_company_id"] = vals["company_id"]
        if "proxy_user_id" not in vals and "invoice_user_id" in vals:
            vals["proxy_user_id"] = vals["invoice_user_id"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sync_proxy_fields_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._sync_proxy_fields_vals(vals)
        res = super().write(vals)
        if "partner_id" in vals:
            self._onchange_ind_final()
        return res

    @api.onchange("company_id")
    def _onchange_company_id_br(self):
        if self.fiscal_document_id:
            self.fiscal_document_id.company_id = self.company_id

    @api.onchange("partner_id")
    def _onchange_partner_id_br(self):
        if self.fiscal_document_id:
            self.fiscal_document_id.partner_id = self.partner_id

    @api.constrains("fiscal_document_id", "document_type_id")
    def _check_fiscal_document_type(self):
        for rec in self:
            if rec.document_type_id and not rec.fiscal_document_id:
                raise UserError(
                    _(
                        "You cannot set a document type when the move has no"
                        " Fiscal Document!"
                    )
                )

    @api.depends("line_ids", "fiscal_document_id")
    def _compute_fiscal_document_ids(self):
        for move in self:
            docs = move.fiscal_document_id
            for line in move.invoice_line_ids:
                docs |= line.document_id
            move.fiscal_document_ids = docs

    @api.depends("move_type", "fiscal_operation_id")
    def _compute_fiscal_operation_type(self):
        for inv in self:
            if inv.move_type == "entry":
                # if it is a Journal Entry there is nothing to do.
                inv.fiscal_operation_type = False
                continue
            if inv.fiscal_operation_id:
                inv.fiscal_operation_type = (
                    inv.fiscal_operation_id.fiscal_operation_type
                )
            else:
                inv.fiscal_operation_type = MOVE_TO_OPERATION[inv.move_type]

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "invoice_line_ids"

    @api.onchange("ind_final")
    def _onchange_ind_final(self):
        """Propagate ind_final from the invoice header to its lines.

        The document mixin defines the same onchange on
        l10n_br_fiscal.document, but account.move uses _inherits (not
        _inherit) to delegate to the fiscal document, so the mixin's
        @api.onchange never fires in the account.move Form context.
        We must re-declare it here so the Form triggers it when
        ind_final changes (e.g. after a partner_id change that
        recomputes ind_final via _compute_ind_final).
        """
        for line in self.invoice_line_ids:
            if line.ind_final != self.ind_final:
                line.ind_final = self.ind_final

    def ensure_one_doc(self):
        self.ensure_one()
        if len(self.fiscal_document_ids) > 1:
            raise UserError(
                _(
                    "More than 1 fiscal document!"
                    "You should open the fiscal view"
                    "and perform the action on each document!"
                )
            )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        move_type = self.env.context.get("default_move_type", "out_invoice")
        if move_type and move_type != "entry":
            defaults["fiscal_operation_type"] = MOVE_TO_OPERATION[move_type]
            if defaults["fiscal_operation_type"] == FISCAL_OUT:
                defaults["issuer"] = DOCUMENT_ISSUER_COMPANY
            else:
                defaults["issuer"] = DOCUMENT_ISSUER_PARTNER
        return defaults

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_id.code != "BR" or view_type != "form":
            return arch, view
        if view_type == "form" and self.env.company.country_id.code == "BR":
            arch = self.env["l10n_br_fiscal.document.line"].inject_fiscal_fields(arch)

        for tax_totals_node in arch.xpath(
            "//field[@name='tax_totals'][@widget='account-tax-totals-field']"
        ):
            tax_totals_node.set("attrs", "{'invisible': True}")

        if view_type == "form" and (
            self.env.user.has_group("l10n_br_account.group_line_fiscal_detail")
            or self.env.context.get("force_line_fiscal_detail")
        ):
            for sub_tree_node in arch.xpath("//field[@name='invoice_line_ids']/list"):
                sub_tree_node.attrib["editable"] = ""

        return arch, view

    @api.depends(
        #        "line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency",
        #        "line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency",
        "line_ids.balance",
        "line_ids.currency_id",
        "line_ids.amount_currency",
        "line_ids.amount_residual",
        "line_ids.amount_residual_currency",
        #        "line_ids.payment_id.state",
        "line_ids.full_reconcile_id",
        "state",
        "direction_sign",
        "fiscal_operation_id",
        "fiscal_line_ids.cfop_id",
        "fiscal_line_ids.fiscal_amount_untaxed",
        "fiscal_line_ids.fiscal_amount_tax",
    )
    def _compute_amount(self):
        if "force_fiscal_amount_recompute" in self._context:
            for move in self.filtered(lambda m: m.fiscal_operation_id):
                # this is a ugly hack required for importing composite
                # fiscal documents for instance. It should be used
                # exceptionnaly as it breaks the dependency chain and
                # can leave fields such as payment_state inconsistent.
                move._compute_fiscal_amount()

        result = super()._compute_amount()
        for move in self.filtered(lambda m: m.fiscal_operation_id):
            sign = -move.direction_sign
            inv_line_ids = move.line_ids.filtered(
                lambda line: line.display_type == "product"
                and (not line.cfop_id or line.cfop_id.finance_move)
            )
            move.amount_untaxed = sum(inv_line_ids.mapped("fiscal_amount_untaxed"))
            move.amount_tax = sum(inv_line_ids.mapped("fiscal_amount_tax"))
            move.amount_untaxed_signed = sign * sum(
                inv_line_ids.mapped("fiscal_amount_untaxed")
            )
            move.amount_tax_signed = sign * sum(
                inv_line_ids.mapped("fiscal_amount_tax")
            )
            move.amount_total = sum(inv_line_ids.mapped("fiscal_amount_total"))

        return result

    def _compute_imported_terms(self):
        self.ensure_one()
        pass  # meant to be overriden

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
        "invoice_line_ids.cfop_id",
        "amount_financial_total",
    )
    def _compute_needed_terms(self):
        """
        Similar to the _compute_needed_terms super method in the account module,
        but ensure moves are balanced in Brazil when there is a fiscal_operation_id.
        """
        res = None
        invoices_with_fiscal_op = self.filtered(lambda inv: inv.fiscal_operation_id)
        invoices_without_fiscal_op = self - invoices_with_fiscal_op
        if invoices_without_fiscal_op:
            res = super(AccountMove, invoices_without_fiscal_op)._compute_needed_terms()

        for invoice in invoices_with_fiscal_op:
            is_draft = invoice.id != invoice._origin.id
            invoice.needed_terms = {}
            invoice.needed_terms_dirty = True
            sign = 1 if invoice.is_inbound(include_receipts=True) else -1
            if invoice.is_invoice(True) and invoice.invoice_line_ids:
                if invoice.imported_document:
                    invoice._compute_imported_terms()
                elif invoice.invoice_payment_term_id:
                    if is_draft:
                        tax_amount_currency = 0.0
                        untaxed_amount_currency = 0.0
                        for line in invoice.invoice_line_ids:
                            if line.cfop_id and not line.cfop_id.finance_move:
                                pass
                            else:
                                untaxed_amount_currency += line.price_subtotal
                        untaxed_amount = untaxed_amount_currency
                        tax_amount = tax_amount_currency
                    else:
                        tax_amount_currency = tax_amount = 0.0
                        untaxed_amount_currency = invoice.amount_financial_total * sign
                        untaxed_amount = invoice.amount_financial_total * sign
                    invoice_payment_terms = (
                        invoice.invoice_payment_term_id._compute_terms(
                            date_ref=invoice.invoice_date
                            or invoice.date
                            or fields.Date.context_today(invoice),
                            currency=invoice.currency_id,
                            tax_amount_currency=tax_amount_currency,
                            tax_amount=tax_amount,
                            untaxed_amount_currency=untaxed_amount_currency,
                            untaxed_amount=untaxed_amount,
                            company=invoice.company_id,
                            sign=sign,
                        )
                    )
                    for term in invoice_payment_terms["line_ids"]:
                        key = frozendict(
                            {
                                "move_id": invoice.id,
                                "date_maturity": fields.Date.to_date(term.get("date")),
                                "discount_date": invoice_payment_terms.get(
                                    "discount_date"
                                ),
                                # "discount_percentage": invoice_payment_terms.get(
                                #     "discount_percentage"
                                # ),
                            }
                        )
                        values = {
                            "balance": term.get("company_amount"),
                            "amount_currency": term.get("foreign_amount"),
                            "discount_amount_currency": term.get(
                                "discount_amount_currency"
                            )
                            or 0.0,
                            "discount_balance": invoice_payment_terms.get(
                                "discount_balance"
                            )
                            or 0.0,
                            "discount_date": invoice_payment_terms.get("discount_date"),
                            # "discount_percentage": invoice_payment_terms.get(
                            #     "discount_percentage"
                            # ),
                        }
                        if key not in invoice.needed_terms:
                            invoice.needed_terms[key] = values
                        else:
                            invoice.needed_terms[key]["balance"] += values["balance"]
                            invoice.needed_terms[key]["amount_currency"] += values[
                                "amount_currency"
                            ]
                if not invoice.needed_terms:
                    invoice.needed_terms[
                        frozendict(
                            {
                                "move_id": invoice.id,
                                "date_maturity": fields.Date.to_date(
                                    invoice.invoice_date_due
                                ),
                                "discount_date": False,
                                # "discount_percentage": 0,
                            }
                        )
                    ] = {
                        "balance": invoice.amount_total_signed,
                        "amount_currency": invoice.amount_total_in_currency_signed,
                    }
        return res

    def _get_protected_vals(self, vals, records):
        """
        Overriden to deal with _inherits and the fiscal document(.line)
        WARNING: override is not calling the super method! (TODO fix if possible)
        """
        protected = set()
        for fname in vals:
            if (
                records._name == "account.move"
                and records.fiscal_document_id
                and records.fiscal_document_id._fields.get(fname)
            ):
                continue
            elif (
                records._name == "account.move.line"
                and records.fiscal_document_line_id
                and records.fiscal_document_line_id._fields.get(fname)
            ):
                continue
            field = records._fields[fname]
            if field.inverse or (field.compute and not field.readonly):
                protected.update(self.pool.field_computed.get(field, [field]))
        return [(protected, rec) for rec in records] if protected else []

    @contextmanager
    def _sync_dynamic_lines(self, container):
        with self._disable_recursion(container, "skip_invoice_sync") as disabled:
            if disabled:
                yield
                return
        with super()._sync_dynamic_lines(container):
            yield
        self.update_payment_term_number()

    def update_payment_term_number(self):
        payment_term_lines = self.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        payment_term_lines_sorted = payment_term_lines.sorted(
            key=lambda line: line.date_maturity
        )
        for idx, line in enumerate(payment_term_lines_sorted, start=1):
            line.with_context(skip_invoice_sync=True).write(
                {
                    "payment_term_number": f"{idx}-{len(payment_term_lines_sorted)}",
                }
            )

    def unlink(self):
        """Allow to delete draft or cancelled invoices"""
        unlink_moves = self.env["account.move"]
        unlink_documents = self.env["l10n_br_fiscal.document"]
        for move in self:
            if not move.exists():
                continue
            if move.fiscal_document_id and move.fiscal_document_id:
                unlink_documents |= move.fiscal_document_id
            unlink_moves |= move
        result = super(AccountMove, unlink_moves).unlink()
        unlink_documents.unlink()
        self.env.registry.clear_cache()
        return result

    @api.depends("move_type", "fiscal_operation_id")
    def _compute_journal_id(self):
        fisc_operation_driven = self.filtered(
            lambda move: move.fiscal_operation_id
            and move.fiscal_operation_id.journal_id
        )
        for move in fisc_operation_driven:
            move.journal_id = self.fiscal_operation_id.journal_id
        return super(AccountMove, self - fisc_operation_driven)._compute_journal_id()

    def open_fiscal_document(self):
        """
        If there is only 1 fiscal document (usual case), open
        the fiscal form view for it.
        Open the tree view in the case of several fiscal documents.
        """
        self.ensure_one()

        # doubt: is this in/out/all action selection relevant?
        if self.env.context.get("move_type") == "out_invoice":
            xmlid = "l10n_br_fiscal.document_out_action"
        elif self.env.context.get("move_type") == "in_invoice":
            xmlid = "l10n_br_fiscal.document_in_action"
        else:
            xmlid = "l10n_br_fiscal.document_all_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)

        if len(self.fiscal_document_ids) == 1:
            form_view = [(self.env.ref("l10n_br_fiscal.document_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = self.fiscal_document_ids[0].id
        else:
            action["domain"] = [("id", "in", self.fiscal_document_ids.ids)]
        return action

    def button_draft(self):
        """Set the move to draft state, handling fiscal documents."""
        # Process fiscal documents first to sync their state
        for move in self.filtered(lambda d: d.document_type_id):
            if (
                move.state_edoc == SITUACAO_EDOC_CANCELADA
                and move.document_number
                and move.issuer == DOCUMENT_ISSUER_COMPANY
                and move.fiscal_document_id.cancel_event_id
            ):
                raise UserError(
                    _(
                        "You can't set this document number: {} to draft "
                        "because this document is cancelled in SEFAZ"
                    ).format(move.document_number)
                )
            # Sync fiscal document state (this is idempotent)
            # Pass in_button_draft context to prevent document.py from
            # calling button_draft again (which would cause double super call)
            move.fiscal_document_ids.filtered(
                lambda d: d.state_edoc != SITUACAO_EDOC_EM_DIGITACAO
            ).with_context(in_button_draft=True).action_document_back2draft()

        # Always call super to set the move to draft
        return super().button_draft()

    def action_document_send(self):
        for invoice in self.filtered(lambda d: d.document_type_id):
            if hasattr(invoice.fiscal_document_ids, "action_document_send"):
                invoice.fiscal_document_ids.action_document_send()
            # FIXME: na migração para a v14 foi permitido o post antes do envio
            #  para destravar a migração, mas poderia ser cogitado de obrigar a
            #  transmissão antes do post novamente como na v12.
            # for invoice in invoices:
            #     invoice.move_id.post(invoice=invoice)

    def action_document_cancel(self):
        for move in self.filtered(lambda d: d.document_type_id):
            move.ensure_one_doc()
            return move.fiscal_document_id.action_document_cancel()

    def action_document_correction(self):
        for move in self.filtered(lambda d: d.document_type_id):
            move.ensure_one_doc()
            return move.fiscal_document_id.action_document_correction()

    def action_document_invalidate(self):
        for move in self.filtered(lambda d: d.document_type_id):
            move.ensure_one_doc()
            return move.fiscal_document_id.action_document_invalidate()

    def action_document_back2draft(self):
        """Sets fiscal document to draft state and cancel and set to draft
        the related invoice for both documents remain equivalent state."""
        for move in self.filtered(lambda d: d.document_type_id):
            # Avoid recursive calls - skip button_cancel if we're already in
            # button_cancel flow (in_button_cancel context is set)
            if not self.env.context.get("in_button_cancel"):
                move.with_context(in_button_cancel=True).button_cancel()
            move.button_draft()

    def action_view_invoice(self):
        for move in self.filtered(lambda d: d.document_type_id):
            move.ensure_one_doc()
            return move.fiscal_document_id.action_view_invoice()

    def _post(self, soft=True):
        for move in self.with_context(skip_post=True):
            move.fiscal_document_ids.filtered(
                lambda d: d.document_type_id
            ).action_document_confirm()
        return super()._post(soft=soft)

    def view_xml(self):
        self.ensure_one_doc()
        return self.fiscal_document_id.view_xml()

    def view_pdf(self):
        self.ensure_one_doc()
        return self.fiscal_document_id.view_pdf()

    def action_send_email(self):
        self.ensure_one_doc()
        return self.fiscal_document_id.action_send_email()

    def copy_data(self, default=None):
        res = super().copy_data(default=default)
        for move, values in zip(self, res, strict=False):
            if not values.get("fiscal_operation_id"):
                values["fiscal_operation_id"] = move.fiscal_operation_id.id
            if not values.get("document_type_id"):
                values["document_type_id"] = move.document_type_id.id
        return res

    def _reverse_moves(self, default_values_list=None, cancel=False):
        new_moves = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
        force_fiscal_operation_id = False
        if self.env.context.get("force_fiscal_operation_id"):
            force_fiscal_operation_id = self.env["l10n_br_fiscal.operation"].browse(
                self.env.context.get("force_fiscal_operation_id")
            )
        for record in new_moves:
            if not record.document_type_id:
                continue

            source_move = record.reversed_entry_id
            if not source_move:
                continue

            # Fallback to source move's operation if not copied
            source_op = source_move.fiscal_operation_id
            if not source_op:
                raise UserError(
                    _("""Document without Fiscal Operation! \n Force one!""")
                )

            if (
                not force_fiscal_operation_id
                and not source_op.return_fiscal_operation_id
            ):
                raise UserError(
                    _("""Document without Return Fiscal Operation! \n Force one!""")
                )

            record.fiscal_operation_id = (
                force_fiscal_operation_id or source_op.return_fiscal_operation_id
            )

            # Match lines between reversed move and source move
            # In reversal, order is usually preserved.
            if len(record.invoice_line_ids) == len(source_move.invoice_line_ids):
                matched_lines = zip(
                    record.invoice_line_ids, source_move.invoice_line_ids, strict=False
                )
            else:
                # Fallback to empty source lines if count mismatch (unlikely)
                matched_lines = [
                    (line, self.env["account.move.line"])
                    for line in record.invoice_line_ids
                ]

            for line, _source_line in matched_lines:
                # Use the line's fiscal operation if set, otherwise fallback to
                # the source move's operation (handles cases where line fiscal
                # operation is not set, e.g., when modifying posted moves)
                line_fiscal_op = line.fiscal_operation_id or source_op

                if (
                    not force_fiscal_operation_id
                    and not line_fiscal_op.return_fiscal_operation_id
                ):
                    raise UserError(
                        _(
                            """Line without Return Fiscal Operation! \n
                            Please force one! \n%(name)s""",
                            name=line.name,
                        )
                    )

                line.fiscal_operation_id = (
                    force_fiscal_operation_id
                    or line_fiscal_op.return_fiscal_operation_id
                )

            # This method is in l10n_br_fiscal_subsequent_document module, the IF
            # is necessary to avoid a 'glue module' or direct dependence.
            if hasattr(record.fiscal_document_id, "_document_reference"):
                # Add the related document to the NF-e.
                # this is required for correct xml validation
                if record.document_type_id and record.document_type_id.code in (
                    MODELO_FISCAL_NFE
                ):
                    record.fiscal_document_id._document_reference(
                        record.reversed_entry_id.fiscal_document_id
                    )

        return new_moves

    def button_cancel(self):
        for doc in self.filtered(lambda d: d.document_type_id):
            if hasattr(doc.fiscal_document_id, "action_document_cancel"):
                doc.fiscal_document_id.action_document_cancel()
        return super().button_cancel()

    def button_import_fiscal_document(self):
        """
        Import move fields and invoice lines from
        the fiscal_document_id record if there is any new line
        to import.
        You can typically set fiscal_document_id to some l10n_br_fiscal.document
        record that was imported previously and import its lines into the
        current move.
        """
        for move in self:
            if move.state != "draft":
                raise UserError(_("Cannot import in non draft Account Move!"))
            elif (
                move.partner_id
                and move.partner_id != move.fiscal_document_id.partner_id
            ):
                raise UserError(_("Partner mismatch!"))
            elif (
                MOVE_TO_OPERATION[move.move_type]
                != move.fiscal_document_id.fiscal_operation_type
            ):
                raise UserError(_("Fiscal Operation Type mismatch!"))
            elif move.company_id != move.fiscal_document_id.company_id:
                raise UserError(_("Company mismatch!"))

            move_fiscal_lines = set(
                move.invoice_line_ids.mapped("fiscal_document_line_id")
            )
            fiscal_doc_lines = set(move.fiscal_document_id.fiscal_line_ids)
            if move_fiscal_lines == fiscal_doc_lines:
                raise UserError(_("No new Fiscal Document Line to import!"))

            self.import_fiscal_document(move.fiscal_document_id, move_id=move.id)

    @api.model
    def import_fiscal_document(
        self,
        fiscal_document,
        move_id=None,
        move_type="in_invoice",
    ):
        """
        Import the data from an existing fiscal document into a new
        invoice or into an existing invoice.
        First it transfers the "shadowed" fields and fill the other
        mandatory invoice fields.
        The account.move onchanges of these fields are properly
        triggered as if the invoice was filled manually.
        Then it creates each account.move.line and fill them using
        their fiscal_document_id onchange.
        """
        if move_id:
            move = self.env["account.move"].browse(move_id)
        else:
            move = self.env["account.move"]
        move_form = Form(
            move.with_context(
                default_move_type=move_type,
                account_predictive_bills_disable_prediction=True,
                force_fiscal_amount_recompute=True,
            )
        )
        if not move_id or not move.fiscal_document_id:
            move_form.partner_id = fiscal_document.partner_id
            move_form.invoice_date = fiscal_document.document_date
            move_form.date = fiscal_document.document_date
            move_form.document_type_id = fiscal_document.document_type_id
            move_form.fiscal_document_id = fiscal_document
            move_form.fiscal_operation_id = fiscal_document.fiscal_operation_id
            move_form.document_serie = fiscal_document.document_serie

        unit_and_prices = []  # save units to force them later
        for line in fiscal_document.fiscal_line_ids:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.cfop_id = (
                    line.cfop_id
                )  # required if we disable some fiscal tax updates
                line_form.fiscal_operation_id = self.fiscal_operation_id
                line_form.fiscal_document_line_id = line
                # for some reason trying to set the product_uom_id
                # here results in strange bugs like unbalanced move
                # so we will force product_uom_id later
                # we also save price_unit to reset unit factor effect
                unit_and_prices.append((line.uot_id.id, line.price_unit))
        move_form.save()
        move = self.env["account.move"].browse(move_form.id)
        for index, item in enumerate(unit_and_prices):
            move.invoice_line_ids[index].product_uom_id = item[0]
            move.invoice_line_ids[index].price_unit = item[1]
        return move_form
