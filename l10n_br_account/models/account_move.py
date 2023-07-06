# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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

SHADOWED_FIELDS = [
    "partner_id",
    "company_id",
    "currency_id",
    "partner_shipping_id",
    "user_id",
]


class InheritsCheckMuteLogger(mute_logger):
    """
    Mute the Model#_inherits_check warning
    because the _inherits field is not required.
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
        field as required.
        """
        with InheritsCheckMuteLogger("odoo.models"):  # mute spurious warnings
            super()._inherits_check()
        field = self._fields.get("fiscal_document_id")
        field.required = False  # unset the required = True assignement

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    @api.model
    def _inject_shadowed_fields(self, vals_list):
        for vals in vals_list:
            for field in self._shadowed_fields():
                if field in vals:
                    vals["fiscal_%s" % (field,)] = vals[field]

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        invoice_view = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if self.env.company.country_id.code != "BR":
            return invoice_view
        elif view_type == "form":
            view = self.env["ir.ui.view"]

            if view_id == self.env.ref("l10n_br_account.fiscal_invoice_form").id:
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
                    sub_form_node, "account.move.line", False
                )
                line_field_name = "invoice_line_ids"
                invoice_view["fields"][line_field_name]["views"]["form"] = {
                    "fields": sub_fields,
                    "arch": sub_arch,
                }

            else:
                if invoice_view["fields"].get("invoice_line_ids"):
                    invoice_line_form_id = self.env.ref(
                        "l10n_br_account.invoice_form"
                    ).id
                    sub_form_view = invoice_view["fields"]["invoice_line_ids"]["views"][
                        "form"
                    ]["arch"]

                    sub_form_node = self.env["account.move.line"].inject_fiscal_fields(
                        sub_form_view
                    )
                    sub_arch, sub_fields = view.postprocess_and_fields(
                        sub_form_node, "account.move.line", False
                    )
                    line_field_name = "invoice_line_ids"
                    invoice_view["fields"][line_field_name]["views"]["form"] = {
                        "fields": sub_fields,
                        "arch": sub_arch,
                    }

                if invoice_view["fields"].get("line_ids"):
                    invoice_line_form_id = self.env.ref(
                        "l10n_br_account.invoice_form"
                    ).id
                    sub_form_view = invoice_view["fields"]["line_ids"]["views"]["tree"][
                        "arch"
                    ]

                    sub_form_node = self.env["account.move.line"].inject_fiscal_fields(
                        sub_form_view
                    )
                    sub_arch, sub_fields = view.postprocess_and_fields(
                        sub_form_node, "account.move.line", False
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
                    line._update_taxes()

        result = super()._compute_amount()
        for move in self.filtered(lambda m: m.company_id.country_id.code == "BR"):
            if move.move_type == "entry" or move.is_outbound():
                sign = -1
            else:
                sign = 1
            inv_line_ids = move.line_ids.filtered(
                lambda l: not l.exclude_from_invoice_tab
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
        new_vals_list = super(
            AccountMove, self.with_context(lines_compute_amounts=True)
        )._move_autocomplete_invoice_lines_create(vals_list)
        for vals in new_vals_list:
            if not vals.get("document_type_id"):
                vals[
                    "fiscal_document_id"
                ] = False  # self.env.company.fiscal_dummy_id.id
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
        """Allows delete a draft or cancelled invoices"""
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
        """Useful in case we want to pre-process taxes_map"""

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
                lambda l: l.account_id.user_type_id.type in ("receivable", "payable")
                and l.move_id.document_type_id
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
        if self.env.context.get("move_type", "") == "out_invoice":
            xmlid = "l10n_br_account.fiscal_invoice_out_action"
        elif self.env.context.get("move_type", "") == "in_invoice":
            xmlid = "l10n_br_account.fiscal_invoice_in_action"
        else:
            xmlid = "l10n_br_account.fiscal_invoice_all_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        form_view = [(self.env.ref("l10n_br_account.fiscal_invoice_form").id, "form")]
        if "views" in action:
            action["views"] = form_view + [
                (state, view) for state, view in action["views"] if view != "form"
            ]
        else:
            action["views"] = form_view
        action["res_id"] = self.id
        return action

    def button_draft(self):
        for i in self.filtered(lambda d: d.document_type_id):
            if i.state_edoc == SITUACAO_EDOC_CANCELADA:
                if i.issuer == DOCUMENT_ISSUER_COMPANY:
                    raise UserError(
                        _(
                            "You can't set this document number: {} to draft "
                            "because this document is cancelled in SEFAZ"
                        ).format(i.document_number)
                    )
            if i.state_edoc != SITUACAO_EDOC_EM_DIGITACAO:
                i.fiscal_document_id.action_document_back2draft()
        return super().button_draft()

    def action_document_send(self):
        invoices = self.filtered(lambda d: d.document_type_id)
        if invoices:
            invoices.mapped("fiscal_document_id").action_document_send()
            # FIXME: na migração para a v14 foi permitido o post antes do envio
            #  para destravar a migração, mas poderia ser cogitado de obrigar a
            #  transmissão antes do post novamente como na v12.
            # for invoice in invoices:
            #     invoice.move_id.post(invoice=invoice)

    def action_document_cancel(self):
        for i in self.filtered(lambda d: d.document_type_id):
            return i.fiscal_document_id.action_document_cancel()

    def action_document_correction(self):
        for i in self.filtered(lambda d: d.document_type_id):
            return i.fiscal_document_id.action_document_correction()

    def action_document_invalidate(self):
        for i in self.filtered(lambda d: d.document_type_id):
            return i.fiscal_document_id.action_document_invalidate()

    def action_document_back2draft(self):
        """Sets fiscal document to draft state and cancel and set to draft
        the related invoice for both documents remain equivalent state."""
        for i in self.filtered(lambda d: d.document_type_id):
            i.button_cancel()
            i.button_draft()

    def action_post(self):
        result = super().action_post()

        self.mapped("fiscal_document_id").filtered(
            lambda d: d.document_type_id
        ).action_document_confirm()

        # TODO FIXME
        # Deixar a migração das funcionalidades do refund por último.
        # Verificar se ainda haverá necessidade desse código.

        # for record in self.filtered(lambda i: i.refund_move_id):
        #     if record.state == "open":
        #         # Ao confirmar uma fatura/documento fiscal se é uma devolução
        #         # é feito conciliado com o documento de origem para abater
        #         # o valor devolvido pelo documento de refund
        #         to_reconcile_lines = self.env["account.move.line"]
        #         for line in record.move_id.line_ids:
        #             if line.account_id.id == record.account_id.id:
        #                 to_reconcile_lines += line
        #             if line.reconciled:
        #                 line.remove_move_reconcile()
        #         for line in record.refund_move_id.move_id.line_ids:
        #             if line.account_id.id == record.refund_move_id.account_id.id:
        #                 to_reconcile_lines += line

        #         to_reconcile_lines.filtered(lambda l: l.reconciled).reconcile()

        return result

    def view_xml(self):
        self.ensure_one()
        return self.fiscal_document_id.view_xml()

    def view_pdf(self):
        self.ensure_one()
        return self.fiscal_document_id.view_pdf()

    def action_send_email(self):
        self.ensure_one()
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
                            Please force one! \n{}""".format(
                                line.name
                            )
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

    def _prepare_wh_invoice(self, move_line, fiscal_group):
        wh_date_invoice = move_line.move_id.date
        wh_due_invoice = wh_date_invoice.replace(day=fiscal_group.wh_due_day)
        values = {
            "partner_id": fiscal_group.partner_id.id,
            "date": wh_date_invoice,
            "date_due": wh_due_invoice + relativedelta(months=1),
            "type": "in_invoice",
            "account_id": fiscal_group.partner_id.property_account_payable_id.id,
            "journal_id": move_line.journal_id.id,
            "origin": move_line.move_id.name,
        }
        return values

    def _prepare_wh_invoice_line(self, invoice, move_line):
        values = {
            "name": move_line.name,
            "quantity": move_line.quantity,
            "uom_id": move_line.product_uom_id,
            "price_unit": abs(move_line.balance),
            "move_id": invoice.id,
            "account_id": move_line.account_id.id,
            "wh_move_line_id": move_line.id,
            "account_analytic_id": move_line.analytic_account_id.id,
        }
        return values

    def _finalize_invoices(self, invoices):
        for invoice in invoices:
            invoice.compute_taxes()
            for line in invoice.line_ids:
                # Use additional field helper function (for account extensions)
                line._set_additional_fields(invoice)
            invoice._onchange_cash_rounding()

    def create_wh_invoices(self):
        for move in self:
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                # Create Wh Invoice only for supplier invoice
                if line.move_id and line.move_id.type != "in_invoice":
                    continue

                account_tax_group = line.tax_line_id.tax_group_id
                if account_tax_group and account_tax_group.fiscal_tax_group_id:
                    fiscal_group = account_tax_group.fiscal_tax_group_id
                    if fiscal_group.tax_withholding:
                        invoice = self.env["account.move"].create(
                            self._prepare_wh_invoice(line, fiscal_group)
                        )

                        self.env["account.move.line"].create(
                            self._prepare_wh_invoice_line(invoice, line)
                        )

                        self._finalize_invoices(invoice)
                        invoice.action_post()

    def _withholding_validate(self):
        for m in self:
            invoices = (
                self.env["account.move.line"]
                .search([("wh_move_line_id", "in", m.mapped("line_ids").ids)])
                .mapped("move_id")
            )
            invoices.filtered(lambda i: i.state == "open").button_cancel()
            invoices.filtered(lambda i: i.state == "cancel").button_draft()
            invoices.invalidate_cache()
            invoices.filtered(lambda i: i.state == "draft").unlink()

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
        # Esse método é responsavel por verificar se há alguma fatura de impostos
        # retidos associada a essa fatura e cancela-las também.
        self._withholding_validate()
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
