# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from contextlib import contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo.tools import frozendict, mute_logger

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_IN_OUT_ALL,
    FISCAL_OUT,
    MODELO_FISCAL_NFE,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_EM_DIGITACAO,
)

MOVE_TO_OPERATION = {
    "out_invoice": "out",
    "in_invoice": "in",
    "out_refund": "in",
    "in_refund": "out",
    "out_receipt": "out",
    "in_receipt": "in",
}

REFUND_TO_OPERATION = {
    "out_invoice": "in",
    "in_invoice": "out",
    "out_refund": "out",
    "in_refund": "in",
}

FISCAL_TYPE_REFUND = {
    "out": ["purchase_refund", "in_return"],
    "in": ["sale_refund", "out_return"],
}

MOVE_TAX_USER_TYPE = {
    "out_invoice": "sale",
    "in_invoice": "purchase",
    "out_refund": "sale",
    "in_refund": "purchase",
}

# l10n_br_fiscal.document field names that are shadowed
# by account.move fields:
SHADOWED_FIELDS = ["company_id", "currency_id", "user_id", "partner_id"]


class InheritsCheckMuteLogger(mute_logger):
    """
    Mute the Model#_inherits_check warning
    because the _inherits field is not required.
    (some account.move may have no fiscal document)
    """

    def filter(self, record):
        msg = record.getMessage()
        if "Field definition for _inherits reference" in msg:
            return 0
        return super().filter(record)


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [
        _name,
        "l10n_br_fiscal.document.move.mixin",
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
    _inherits = {"l10n_br_fiscal.document": "fiscal_document_id"}

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
        compute="_compute_fiscal_document_id",
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

    @api.onchange("document_type_id")
    def _inverse_document_type_id(self):
        if (self.document_type_id and not self.fiscal_document_id) or (
            not self.document_type_id and self.fiscal_document_id
        ):
            self.env.add_to_compute(self._fields["fiscal_document_id"], self)

    def _compute_fiscal_document_id(self):
        for move in self:
            if move.document_type_id and not move.fiscal_document_id:
                fiscal_doc_vals = {}
                for field in self._shadowed_fields():
                    fiscal_doc_vals[f"fiscal_proxy_{field}"] = getattr(move, field)
                move.fiscal_document_id = (
                    self.env["l10n_br_fiscal.document"].create(fiscal_doc_vals).id
                )
            elif not move.document_type_id and move.fiscal_document_id:
                bad_fiscal_doc = move.fiscal_document_id
                move.fiscal_document_id = False
                bad_fiscal_doc.action_document_cancel()

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

    @api.depends("line_ids", "invoice_line_ids")
    def _compute_fiscal_document_ids(self):
        for move in self:
            docs = set()
            for line in move.invoice_line_ids:
                docs.add(line.document_id.id)
            move.fiscal_document_ids = list(docs)

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

    def _get_amount_lines(self):
        """Get object lines instances used to compute fields"""
        return self.mapped("invoice_line_ids")

    @api.model
    def _inherits_check(self):
        """
        Overriden to avoid the super method to set the fiscal_document_id
        field as required (because some account.move may not have any fiscal document).
        """
        with InheritsCheckMuteLogger("odoo.models"):  # mute spurious warnings
            res = super()._inherits_check()
        field = self._fields.get("fiscal_document_id")
        field.required = False  # unset the required = True assignement
        return res

    @api.model
    def _shadowed_fields(self):
        """Return the list of shadowed fields that are synchronized
        from account.move."""
        return SHADOWED_FIELDS

    @api.model
    def _inject_shadowed_fields(self, vals_list):
        for vals in vals_list:
            for field in self._shadowed_fields():
                if field in vals:
                    vals[f"fiscal_proxy_{field}"] = vals[field]

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
        if not move_type == "entry":
            defaults["fiscal_operation_type"] = MOVE_TO_OPERATION[move_type]
            if defaults["fiscal_operation_type"] == FISCAL_OUT:
                defaults["issuer"] = DOCUMENT_ISSUER_COMPANY
            else:
                defaults["issuer"] = DOCUMENT_ISSUER_PARTNER
        return defaults

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_id.code != "BR":
            return arch, view
        if view_type == "form":
            view = self.env["ir.ui.view"]

            if view_id == self.env.ref("l10n_br_account.fiscal_invoice_form").id:
                invoice_line_form_id = self.env.ref(
                    "l10n_br_account.fiscal_invoice_line_form"
                ).id
                sub_form_node, _sub_view = self.env["account.move.line"]._get_view(
                    view_id=invoice_line_form_id, view_type="form"
                )
                self.env["account.move.line"].inject_fiscal_fields(sub_form_node)

                # TODO FIXME test this part:
                for original_sub_form_node in arch.xpath(
                    "//field[@name='invoice_line_ids']/form"
                ):
                    parent = original_sub_form_node.parent
                    parent.remove(original_sub_form_node)
                    parent.append(sub_form_node)

            else:
                for sub_form_node in arch.xpath(
                    "//field[@name='invoice_line_ids']/form"
                ):
                    self.env["account.move.line"].inject_fiscal_fields(sub_form_node)
                for sub_form_node in arch.xpath("//field[@name='line_ids']/tree"):
                    self.env["account.move.line"].inject_fiscal_fields(sub_form_node)
                    # TODO kanban??
        #                for sub_form_node in arch.xpath(
        #                   "//field[@name='line_ids']/kanban"):
        #                    self.env["account.move.line"].inject_fiscal_fields(
        #                       sub_form_node)
        #

        return arch, view

    @api.depends(
        "line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency",
        "line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency",
        "line_ids.balance",
        "line_ids.currency_id",
        "line_ids.amount_currency",
        "line_ids.amount_residual",
        "line_ids.amount_residual_currency",
        "line_ids.payment_id.state",
        "line_ids.full_reconcile_id",
        "state",
        "ind_final",
    )
    def _compute_amount(self):
        for move in self.filtered(lambda m: m.fiscal_operation_id):
            for line in move.line_ids:
                if (
                    move.is_invoice(include_receipts=True)
                    and line.display_type == "product"
                ):
                    line._update_fiscal_taxes()

        result = super()._compute_amount()
        for move in self.filtered(lambda m: m.fiscal_operation_id):
            if move.move_type == "entry" or move.is_outbound():
                sign = -1
            else:
                sign = 1
            inv_line_ids = move.line_ids.filtered(
                lambda line: line.display_type == "product"
            )
            move.amount_untaxed = sum(inv_line_ids.mapped("amount_untaxed"))
            move.amount_tax = sum(inv_line_ids.mapped("amount_tax"))
            move.amount_untaxed_signed = sign * sum(
                inv_line_ids.mapped("amount_untaxed")
            )
            move.amount_tax_signed = sign * sum(inv_line_ids.mapped("amount_tax"))

        return result

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
    )
    def _compute_needed_terms(self):
        """
        Similar to the _compute_needed_terms super method in the account module,
        but ensure moves are balanced in Brazil when there is a fiscal_operation_id.
        WARNING: it seems we might not be able to call the super method here....
        """
        for invoice in self:
            is_draft = invoice.id != invoice._origin.id
            invoice.needed_terms = {}
            invoice.needed_terms_dirty = True
            sign = 1 if invoice.is_inbound(include_receipts=True) else -1
            if invoice.is_invoice(True) and invoice.invoice_line_ids:
                if invoice.invoice_payment_term_id:
                    if is_draft:
                        tax_amount_currency = 0.0
                        untaxed_amount_currency = 0.0
                        for line in invoice.invoice_line_ids:
                            if line.cfop_id and not line.cfop_id.finance_move:
                                pass
                            else:
                                untaxed_amount_currency += line.price_subtotal
                            for tax_result in (line.compute_all_tax or {}).values():
                                tax_amount_currency += -sign * tax_result.get(
                                    "amount_currency", 0.0
                                )
                        untaxed_amount = untaxed_amount_currency
                        tax_amount = tax_amount_currency
                    else:
                        tax_amount_currency = invoice.amount_tax * sign
                        tax_amount = invoice.amount_tax_signed
                        if invoice.fiscal_operation_id:
                            if invoice.fiscal_operation_id.deductible_taxes:
                                amount_currency = (
                                    invoice.amount_total
                                    + invoice.amount_tax_withholding
                                )
                            else:
                                amount_currency = (
                                    invoice.amount_total - invoice.amount_ipi_value
                                ) * sign
                            untaxed_amount_currency = amount_currency * sign
                            untaxed_amount = amount_currency * sign

                        else:
                            untaxed_amount_currency = invoice.amount_untaxed * sign
                            untaxed_amount = invoice.amount_untaxed_signed
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
                    for term in invoice_payment_terms:
                        key = frozendict(
                            {
                                "move_id": invoice.id,
                                "date_maturity": fields.Date.to_date(term.get("date")),
                                "discount_date": term.get("discount_date"),
                                "discount_percentage": term.get("discount_percentage"),
                            }
                        )
                        values = {
                            "balance": term["company_amount"],
                            "amount_currency": term["foreign_amount"],
                            "discount_amount_currency": term["discount_amount_currency"]
                            or 0.0,
                            "discount_balance": term["discount_balance"] or 0.0,
                            "discount_date": term["discount_date"],
                            "discount_percentage": term["discount_percentage"],
                        }
                        if key not in invoice.needed_terms:
                            invoice.needed_terms[key] = values
                        else:
                            invoice.needed_terms[key]["balance"] += values["balance"]
                            invoice.needed_terms[key]["amount_currency"] += values[
                                "amount_currency"
                            ]
                else:
                    invoice.needed_terms[
                        frozendict(
                            {
                                "move_id": invoice.id,
                                "date_maturity": fields.Date.to_date(
                                    invoice.invoice_date_due
                                ),
                                "discount_date": False,
                                "discount_percentage": 0,
                            }
                        )
                    ] = {
                        "balance": invoice.amount_total_signed,
                        "amount_currency": invoice.amount_total_in_currency_signed,
                    }

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

    @api.model_create_multi
    def create(self, vals_list):
        self._inject_shadowed_fields(vals_list)
        invoice = super(AccountMove, self.with_context(create_from_move=True)).create(
            vals_list
        )
        return invoice

    def write(self, values):
        self._inject_shadowed_fields([values])
        result = super().write(values)
        return result

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
        self.clear_caches()
        return result

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        result = super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id and self.fiscal_operation_id.journal_id:
            self.journal_id = self.fiscal_operation_id.journal_id
        return result

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
        for move in self.filtered(lambda d: d.document_type_id):
            if move.state_edoc == SITUACAO_EDOC_CANCELADA:
                if move.issuer == DOCUMENT_ISSUER_COMPANY:
                    raise UserError(
                        _(
                            "You can't set this document number: {} to draft "
                            "because this document is cancelled in SEFAZ"
                        ).format(move.document_number)
                    )
            move.fiscal_document_ids.filtered(
                lambda d: d.state_edoc != SITUACAO_EDOC_EM_DIGITACAO
            ).document_back2draft()
        return super().button_draft()

    def action_document_send(self):
        for invoice in self.filtered(lambda d: d.document_type_id):
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
            move.button_cancel()
            move.button_draft()

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

    def _reverse_moves(self, default_values_list=None, cancel=False):
        new_moves = super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )
        force_fiscal_operation_id = False
        if self.env.context.get("force_fiscal_operation_id"):
            force_fiscal_operation_id = self.env["l10n_br_fiscal.operation"].browse(
                self.env.context.get("force_fiscal_operation_id")
            )
        for record in new_moves.filtered(lambda i: i.document_type_id):
            if (
                not force_fiscal_operation_id
                and not record.fiscal_operation_id.return_fiscal_operation_id
            ):
                raise UserError(
                    _("""Document without Return Fiscal Operation! \n Force one!""")
                )

            record.fiscal_operation_id = (
                force_fiscal_operation_id
                or record.fiscal_operation_id.return_fiscal_operation_id
            )
            record._onchange_fiscal_operation_id()

            for line in record.invoice_line_ids:
                if (
                    not force_fiscal_operation_id
                    and not line.fiscal_operation_id.return_fiscal_operation_id
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
                    or line.fiscal_operation_id.return_fiscal_operation_id
                )
                line._onchange_fiscal_operation_id()

            # Adds the related document to the NF-e.
            # this is required for correct xml validation
            if record.document_type_id and record.document_type_id.code in (
                MODELO_FISCAL_NFE
            ):
                record.fiscal_document_id._document_reference(
                    record.reversed_entry_id.fiscal_document_id
                )

        return new_moves

    def _finalize_invoices(self, invoices):
        for invoice in invoices:
            invoice.compute_taxes()
            for line in invoice.line_ids:
                # Use additional field helper function (for account extensions)
                line._set_additional_fields(invoice)
            invoice._onchange_cash_rounding()

    def post(self, invoice=False):
        # TODO FIXME migrate: no more invoice keyword
        result = super().post()
        if invoice:
            if (
                invoice.document_type_id
                and invoice.document_electronic
                and invoice.issuer == DOCUMENT_ISSUER_COMPANY
                and invoice.state_edoc != SITUACAO_EDOC_AUTORIZADA
            ):
                self.button_cancel()
        return result

    def button_cancel(self):
        for doc in self.filtered(lambda d: d.document_type_id):
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
            )
        )
        if not move_id or not move.fiscal_document_id:
            move_form.invoice_date = fiscal_document.document_date
            move_form.date = fiscal_document.document_date
            for field in self._shadowed_fields():
                if field in ("company_id", "user_id"):  # (readonly fields)
                    continue
                if not move_form._view["fields"].get(field):
                    continue
                setattr(move_form, field, getattr(fiscal_document, field))
            move_form.document_type_id = fiscal_document.document_type_id
            move_form.fiscal_document_id = fiscal_document
            move_form.fiscal_operation_id = fiscal_document.fiscal_operation_id

        for line in fiscal_document.fiscal_line_ids:
            with move_form.invoice_line_ids.new() as line_form:
                line_form.cfop_id = (
                    line.cfop_id
                )  # required if we disable some fiscal tax updates
                line_form.fiscal_operation_id = self.fiscal_operation_id
                line_form.fiscal_document_line_id = line
        move_form.save()
        return move_form
