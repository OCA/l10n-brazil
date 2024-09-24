# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from odoo.tools import mute_logger

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

    @api.constrains("fiscal_document_id", "document_type_id")
    def _check_fiscal_document_type(self):
        for rec in self:
            if rec.document_type_id and not rec.fiscal_document_id:
                raise UserError(
                    _(
                        "You cannot set a document type when the move has no Fiscal Document!"
                    )
                )

    @api.depends("line_ids", "invoice_line_ids")
    def _compute_fiscal_document_ids(self):
        for move in self:
            docs = self.env["l10n_br_fiscal.document"]
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

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
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
                    vals["fiscal_proxy_%s" % (field,)] = vals[field]

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
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """
        Inject fiscal fields into the account.move(.line) views.
        FIXME: it's because of this override that the tax m2m widget
        isn't fully displayed (tax names are missing) until the user saves the form.
        """
        invoice_view = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if self.env.company.country_id.code != "BR":
            return invoice_view
        elif view_type == "form":
            view = self.env["ir.ui.view"]

            if view_id == self.env.ref("l10n_br_account.fiscal_invoice_form").id:
                # "fiscal view" case:
                invoice_line_form_id = self.env.ref(
                    "l10n_br_account.fiscal_invoice_line_form"
                ).id
                sub_form_view = self.env["account.move.line"].fields_view_get(
                    view_id=invoice_line_form_id, view_type="form"
                )["arch"]
                sub_form_node = self.env["account.move.line"].inject_fiscal_fields(
                    sub_form_view
                )
                sub_arch, sub_fields = view.postprocess_and_fields(
                    sub_form_node, "account.move.line"
                )
                line_field_name = "invoice_line_ids"
                invoice_view["fields"][line_field_name]["views"]["form"] = {
                    "fields": sub_fields,
                    "arch": sub_arch,
                }

            else:  # "normal" account.move case:
                if invoice_view["fields"].get("invoice_line_ids"):
                    sub_form_view = invoice_view["fields"]["invoice_line_ids"]["views"][
                        "form"
                    ]["arch"]

                    sub_form_node = self.env["account.move.line"].inject_fiscal_fields(
                        sub_form_view
                    )
                    sub_arch, sub_fields = view.postprocess_and_fields(
                        sub_form_node, "account.move.line"
                    )
                    line_field_name = "invoice_line_ids"
                    invoice_view["fields"][line_field_name]["views"]["form"] = {
                        "fields": sub_fields,
                        "arch": sub_arch,
                    }

                if invoice_view["fields"].get("line_ids"):
                    # it is required to inject the fiscal fields in the
                    # "accounting lines" view to avoid loosing fiscal values from the form.
                    sub_form_view = invoice_view["fields"]["line_ids"]["views"]["tree"][
                        "arch"
                    ]

                    sub_form_node = self.env["account.move.line"].inject_fiscal_fields(
                        sub_form_view
                    )
                    sub_arch, sub_fields = view.postprocess_and_fields(
                        sub_form_node, "account.move.line"
                    )
                    line_field_name = "line_ids"
                    invoice_view["fields"][line_field_name]["views"]["tree"] = {
                        "fields": sub_fields,
                        "arch": sub_arch,
                    }

        return invoice_view

    @api.depends(
        "line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency",
        "line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual",
        "line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency",
        "line_ids.debit",
        "line_ids.credit",
        "line_ids.currency_id",
        "line_ids.amount_currency",
        "line_ids.amount_residual",
        "line_ids.amount_residual_currency",
        "line_ids.payment_id.state",
        "line_ids.full_reconcile_id",
        "ind_final",
    )
    def _compute_amount(self):
        for move in self.filtered(lambda m: m.company_id.country_id.code == "BR"):
            for line in move.line_ids:
                if (
                    move.is_invoice(include_receipts=True)
                    and not line.exclude_from_invoice_tab
                ):
                    line._update_fiscal_taxes()

        result = super()._compute_amount()
        for move in self.filtered(lambda m: m.company_id.country_id.code == "BR"):
            if move.move_type == "entry" or move.is_outbound():
                sign = -1
            else:
                sign = 1
            inv_line_ids = move.line_ids.filtered(
                lambda line: not line.exclude_from_invoice_tab
            )
            move.amount_untaxed = sum(inv_line_ids.mapped("amount_untaxed"))
            move.amount_tax = sum(inv_line_ids.mapped("amount_tax"))
            move.amount_untaxed_signed = sign * sum(
                inv_line_ids.mapped("amount_untaxed")
            )
            move.amount_tax_signed = sign * sum(inv_line_ids.mapped("amount_tax"))

        return result

    @api.onchange("ind_final")
    def _onchange_ind_final(self):
        """Trigger the recompute of the taxes when the ind_final is changed"""
        for line in self.invoice_line_ids:
            line._onchange_fiscal_operation_id()
        return self._recompute_dynamic_lines(recompute_all_taxes=True)

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
    def _move_autocomplete_invoice_lines_create(self, vals_list):
        fiscal_document_line_ids = {}
        for idx1, move_val in enumerate(vals_list):
            if "invoice_line_ids" in move_val:
                fiscal_document_line_ids[idx1] = {}
                for idx2, line_val in enumerate(move_val["invoice_line_ids"]):
                    if (
                        line_val[0] == 0
                        and line_val[1] == 0
                        and isinstance(line_val[2], dict)
                    ):
                        fiscal_document_line_ids[idx1][idx2] = line_val[2].get(
                            "fiscal_document_line_id", False
                        )

        new_vals_list = super(
            AccountMove, self.with_context(lines_compute_amounts=True)
        )._move_autocomplete_invoice_lines_create(vals_list)
        for vals in new_vals_list:
            if not vals.get("document_type_id"):
                vals["fiscal_document_id"] = False

        for idx1, move_val in enumerate(new_vals_list):
            if "line_ids" in move_val:
                if fiscal_document_line_ids.get(idx1):
                    idx2 = 0
                    for line_val in move_val["line_ids"]:
                        if (
                            line_val[0] == 0
                            and line_val[1] == 0
                            and isinstance(line_val[2], dict)
                        ):
                            line_val[2][
                                "fiscal_document_line_id"
                            ] = fiscal_document_line_ids[idx1].get(idx2)
                            idx2 += 1

        return new_vals_list

    def _move_autocomplete_invoice_lines_values(self):
        self.ensure_one()
        if self._context.get("lines_compute_amounts"):
            self.line_ids._compute_amounts()
        return super()._move_autocomplete_invoice_lines_values()

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

    @api.model
    def _serialize_tax_grouping_key(self, grouping_dict):
        return "-".join(str(v) for v in grouping_dict.values())

    @api.model
    def _compute_taxes_mapped(self, base_line):
        move = base_line.move_id

        if move.is_invoice(include_receipts=True):
            handle_price_include = True
            sign = -1 if move.is_inbound() else 1
            quantity = base_line.quantity
            is_refund = move.move_type in ("out_refund", "in_refund")
            price_unit_wo_discount = (
                sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            )
        else:
            handle_price_include = False
            quantity = 1.0
            tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
            is_refund = (tax_type == "sale" and base_line.debit) or (
                tax_type == "purchase" and base_line.credit
            )
            price_unit_wo_discount = base_line.amount_currency

        balance_taxes_res = base_line.tax_ids._origin.with_context(
            force_sign=move._get_tax_force_sign()
        ).compute_all(
            price_unit_wo_discount,
            currency=base_line.currency_id,
            quantity=quantity,
            product=base_line.product_id,
            partner=base_line.partner_id,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
            fiscal_taxes=base_line.fiscal_tax_ids,
            operation_line=base_line.fiscal_operation_line_id,
            ncm=base_line.ncm_id,
            nbs=base_line.nbs_id,
            nbm=base_line.nbm_id,
            cest=base_line.cest_id,
            discount_value=base_line.discount_value,
            insurance_value=base_line.insurance_value,
            other_value=base_line.other_value,
            ii_customhouse_charges=base_line.ii_customhouse_charges,
            cfop=base_line.cfop_id,
            freight_value=base_line.freight_value,
            fiscal_price=base_line.fiscal_price,
            fiscal_quantity=base_line.fiscal_quantity,
            uot_id=base_line.uot_id,
            icmssn_range=base_line.icmssn_range_id,
            icms_origin=base_line.icms_origin,
            ind_final=base_line.ind_final,
        )
        return balance_taxes_res

    def _preprocess_taxes_map(self, taxes_map):
        """Compute taxes base and amount for Brazil"""

        taxes_mapped = super()._preprocess_taxes_map(taxes_map=taxes_map)

        for line in self.line_ids.filtered(
            lambda line: not line.tax_repartition_line_id
        ):
            if not line.tax_ids or not line.fiscal_tax_ids:
                continue

            compute_all_vals = self._compute_taxes_mapped(line)

            for tax_vals in compute_all_vals["taxes"]:
                grouping_dict = self._get_tax_grouping_key_from_base_line(
                    line, tax_vals
                )
                grouping_key = self._serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env["account.tax.repartition.line"].browse(
                    tax_vals["tax_repartition_line_id"]
                )

                if taxes_mapped[grouping_key]:
                    taxes_mapped[grouping_key]["amount"] += tax_vals["amount"]
                    taxes_mapped[grouping_key][
                        "tax_base_amount"
                    ] += self._get_base_amount_to_display(
                        tax_vals["base"], tax_repartition_line, tax_vals["group"]
                    )

        return taxes_mapped

    def _recompute_payment_terms_lines(self):
        """Compute the dynamic payment term lines of the journal entry.
        overwritten this method to change aml's field name.
        """

        # TODO - esse método é executado em um onchange, na emissão de um novo
        # documento fiscal o numero do documento pode estar em branco
        # atualizar esse dado ao validar a fatura, ou atribuir o número da NFe
        # antes de salva-la.
        result = super()._recompute_payment_terms_lines()
        if self.document_number:
            terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type
                in ("receivable", "payable")
                and line.move_id.document_type_id
            )
            terms_lines.sorted(lambda line: line.date_maturity)
            for idx, terms_line in enumerate(terms_lines):
                # TODO TODO pegar o método do self.fiscal_document_id.with_context(
                # fiscal_document_no_company=True
                # )._compute_document_name()
                terms_line.name = "{}/{}-{}".format(
                    self.document_number, idx + 1, len(terms_lines)
                )
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
            ).action_document_back2draft()
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

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        # We need to ensure that invoices without a fiscal document have the
        # document_number blank, as all invoices without a fiscal document share this
        # same field, they are linked to the same dummy fiscal document.
        # Otherwise, in the tree view, this field will be displayed with the same value
        # for all these invoices.
        if not self.document_type_id:
            self.document_number = ""

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

    # TODO: Por ora esta solução contorna o problema
    #  AttributeError: 'Boolean' object has no attribute 'depends_context'
    #  Este erro está relacionado com o campo active implementado via localização
    #  nos modelos account.move.line e l10n_br_fiscal.document.line
    #  Este problema começou após este commit:
    #  https://github.com/oca/ocb/commit/1dcd071b27779e7d6d8f536c7dce7002d27212ba
    def _get_integrity_hash_fields_and_subfields(self):
        return self._get_integrity_hash_fields() + [
            f"line_ids.{subfield}"
            for subfield in self.env["account.move.line"]._get_integrity_hash_fields()
        ]

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
