# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    FISCAL_OUT,
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
]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = [
        _name,
        "l10n_br_fiscal.document.mixin.methods",
        "l10n_br_fiscal.document.invoice.mixin",
    ]
    _inherits = {"l10n_br_fiscal.document": "fiscal_document_id"}
    _order = "date DESC, name DESC"

    # some account.move records _inherits from an fiscal.document that is
    # disabled with active=False (dummy record) in the l10n_br_fiscal_document table.
    # To make the invoices still visible, we set active=True
    # in the account_move table.
    active = fields.Boolean(
        string="Active",
        default=True,
    )

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related="partner_id.cnpj_cpf",
    )

    legal_name = fields.Char(
        string="Adapted Legal Name",
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="Adapted State Tax Number",
        related="partner_id.inscr_est",
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
    )

    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        required=True,
        copy=False,
        ondelete="cascade",
    )

    document_type = fields.Char(
        related="document_type_id.code",
        string="Document Code",
        store=True,
    )

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("invoice_line_ids")

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    def _write_shadowed_fields(self):
        for invoice in self:
            if invoice.document_type_id:
                shadowed_fiscal_vals = invoice._prepare_shadowed_fields_dict()
                invoice.fiscal_document_id.write(shadowed_fiscal_vals)

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        invoice_view = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == "form":
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

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            if not vals.get("document_type_id"):
                vals["fiscal_document_id"] = self.env.company.fiscal_dummy_id.id
        invoice = super().create(values)
        invoice._write_shadowed_fields()
        return invoice

    def write(self, values):
        result = super().write(values)
        self._write_shadowed_fields()
        return result

    def unlink(self):
        """Allows delete a draft or cancelled invoices"""
        unlink_moves = self.env["account.move"]
        unlink_documents = self.env["l10n_br_fiscal.document"]
        for move in self:
            if not move.exists():
                continue
            if (
                move.fiscal_document_id
                and move.fiscal_document_id.id != self.env.company.fiscal_dummy_id.id
            ):
                unlink_documents |= move.fiscal_document_id
            unlink_moves |= move
        result = super(AccountMove, unlink_moves).unlink()
        unlink_documents.unlink()
        self.clear_caches()
        return result

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        if self.document_type_id:
            default["fiscal_line_ids"] = False
        else:
            default["fiscal_line_ids"] = self.line_ids[0]
        return super().copy(default)

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
            freight_value=base_line.freight_value,
            fiscal_price=base_line.fiscal_price,
            fiscal_quantity=base_line.fiscal_quantity,
            uot=base_line.uot_id,
            icmssn_range=base_line.icmssn_range_id,
            icms_origin=base_line.icms_origin,
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

    # @api.model
    # def invoice_line_move_line_get(self):
    #     # TODO FIXME migrate. No such method in Odoo 13+
    #     move_lines_dict = super().invoice_line_move_line_get()
    #     new_mv_lines_dict = []
    #     for line in move_lines_dict:
    #         invoice_line = self.line_ids.filtered(lambda l: l.id == line.get("invl_id"))
    #
    #         if invoice_line.fiscal_operation_id:
    #             if invoice_line.fiscal_operation_id.deductible_taxes:
    #                 line["price"] = invoice_line.price_total
    #             else:
    #                 line["price"] = invoice_line.price_total - (
    #                     invoice_line.amount_tax_withholding
    #                     + invoice_line.amount_tax_included
    #                 )
    #
    #         if invoice_line.cfop_id:
    #             if invoice_line.cfop_id.finance_move:
    #                 new_mv_lines_dict.append(line)
    #         else:
    #             new_mv_lines_dict.append(line)
    #
    #     return new_mv_lines_dict
    #

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id and self.fiscal_operation_id.journal_id:
            self.journal_id = self.fiscal_operation_id.journal_id

    def open_fiscal_document(self):
        if self.env.context.get("move_type", "") == "out_invoice":
            action = self.env.ref("l10n_br_account.fiscal_invoice_out_action").read()[0]
        elif self.env.context.get("move_type", "") == "in_invoice":
            action = self.env.ref("l10n_br_account.fiscal_invoice_in_action").read()[0]
        else:
            action = self.env.ref("l10n_br_account.fiscal_invoice_all_action").read()[0]
        form_view = [(self.env.ref("l10n_br_account.fiscal_invoice_form").id, "form")]
        if "views" in action:
            action["views"] = form_view + [
                (state, view) for state, view in action["views"] if view != "form"
            ]
        else:
            action["views"] = form_view
        action["res_id"] = self.id
        return action

    def action_date_assign(self):
        """Usamos esse método para definir a data de emissão do documento
        fiscal e numeração do documento fiscal para ser usado nas linhas
        dos lançamentos contábeis."""
        # TODO FIXME migrate. No such method in Odoo 13+
        super().action_date_assign()
        for invoice in self:
            if invoice.document_type_id:
                if invoice.issuer == DOCUMENT_ISSUER_COMPANY:
                    if (
                        not invoice.comment_ids
                        and invoice.fiscal_operation_id.comment_ids
                    ):
                        invoice.comment_ids |= self.fiscal_operation_id.comment_ids

                    for line in invoice.line_ids:
                        if (
                            not line.comment_ids
                            and line.fiscal_operation_line_id.comment_ids
                        ):
                            line.comment_ids |= (
                                line.fiscal_operation_line_id.comment_ids
                            )

                    invoice.fiscal_document_id._document_date()
                    invoice.fiscal_document_id._document_number()

    def button_draft(self):
        for i in self.filtered(lambda d: d.document_type_id):
            if i.state_edoc == SITUACAO_EDOC_CANCELADA:
                if i.issuer == DOCUMENT_ISSUER_COMPANY:
                    raise UserError(
                        _(
                            "You can't set this document number: {} to draft "
                            "because this document is cancelled in SEFAZ".format(
                                i.document_number
                            )
                        )
                    )
            if i.state_edoc != SITUACAO_EDOC_EM_DIGITACAO:
                i.fiscal_document_id.action_document_back2draft()
        return super().button_draft()

    def action_document_send(self):
        invoices = self.filtered(lambda d: d.document_type_id)
        if invoices:
            invoices.mapped("fiscal_document_id").action_document_send()
            for invoice in invoices:
                invoice.move_id.post(invoice=invoice)

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

    # TODO FIXME migrate. refund method are very different in Odoo 13+
    # def _get_refund_common_fields(self):
    #     fields = super()._get_refund_common_fields()
    #     fields += [
    #         "fiscal_operation_id",
    #         "document_type_id",
    #         "document_serie_id",
    #     ]
    #     return fields

    # @api.returns("self")
    # def refund(self, date=None, date=None, description=None, journal_id=None):
    #     new_invoices = super().refund(date, date, description, journal_id)

    #     force_fiscal_operation_id = False
    #     if self.env.context.get("force_fiscal_operation_id"):
    #         force_fiscal_operation_id = self.env["l10n_br_fiscal.operation"].browse(
    #             self.env.context.get("force_fiscal_operation_id")
    #         )

    #     for record in new_invoices.filtered(lambda i: i.document_type_id):
    #         if (
    #             not force_fiscal_operation_id
    #             and not record.fiscal_operation_id.return_fiscal_operation_id
    #         ):
    #             raise UserError(
    #                 _("""Document without Return Fiscal Operation! \n Force one!""")
    #             )

    #         record.fiscal_operation_id = (
    #             force_fiscal_operation_id
    #             or record.fiscal_operation_id.return_fiscal_operation_id
    #         )
    #         record.fiscal_document_id._onchange_fiscal_operation_id()

    #         for line in record.line_ids:
    #             if (
    #                 not force_fiscal_operation_id
    #                 and not line.fiscal_operation_id.return_fiscal_operation_id
    #             ):
    #                 raise UserError(
    #                     _(
    #                         """Line without Return Fiscal Operation! \n
    #                         Please force one! \n{}""".format(
    #                             line.name
    #                         )
    #                     )
    #                 )

    #             line.fiscal_operation_id = (
    #                 force_fiscal_operation_id
    #                 or line.fiscal_operation_id.return_fiscal_operation_id
    #             )
    #             line._onchange_fiscal_operation_id()

    #         refund_inv_id = record.refund_move_id

    #         if record.refund_move_id.document_type_id:
    #             record.fiscal_document_id._document_reference(
    #                 refund_inv_id.fiscal_document_id
    #             )

    #     return new_invoices

    # def _refund_cleanup_lines(self, lines):
    #     result = super()._refund_cleanup_lines(lines)
    #     for _a, _b, vals in result:
    #         if vals.get("fiscal_document_line_id"):
    #             vals.pop("fiscal_document_line_id")

    #     for i, line in enumerate(lines):
    #         for name, _field in line._fields.items():
    #             if name == "fiscal_tax_ids":
    #                 result[i][2][name] = [(6, 0, line[name].ids)]

    #     return result
