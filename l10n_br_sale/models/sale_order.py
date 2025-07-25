# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from functools import partial

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.sale_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.company.copy_note

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ("fiscal_operation_type", "=", "out"),
            ("state", "=", "approved"),
            ("fiscal_type", "not ilike", "%refund%"),
        ]
        return domain

    company_country_id = fields.Many2one(related="company_id.country_id")

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    ind_pres = fields.Selection(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    copy_note = fields.Boolean(
        string="Copy Sale note on invoice",
        default=_default_copy_note,
    )

    discount_rate = fields.Float(
        string="Discount",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_order_comment_rel",
        column1="sale_id",
        column2="comment_id",
        string="Comments",
        compute="_compute_comment_ids",
        store=True,
    )

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "order_line"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_id.code != "BR":
            return arch, view
        arch = self.env["sale.order.line"].inject_fiscal_fields(arch)
        for tax_totals_node in arch.xpath(
            "//field[@name='tax_totals'][@widget='account-tax-totals-field']"
        ):
            tax_totals_node.set("attrs", "{'invisible': True}")

        if view_type == "form" and (
            self.user_has_groups("l10n_br_sale.group_line_fiscal_detail")
            or self.env.context.get("force_line_fiscal_detail_edition")
        ):
            for sub_tree_node in arch.xpath("//field[@name='order_line']/tree"):
                sub_tree_node.attrib["editable"] = ""

        return arch, view

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id
        else:
            # Caso de uso onde o Pedido foi criado com a Operação Fiscal tanto
            # no Pedido quanto na Linha, os metodo default podem preencher porém
            # o usuário decide que não deve ter Operação Fiscal e não gerar
            # Documento Fiscal, o caso pode ser visto nos Dados de Demonstração,
            # caso a Operação Fiscal seja apagada e o Pedido já tem linhas é
            # preciso apagar o campo na Linha, sem isso acontece um looping porque
            # ao apagar no Pedido o campo fica invisivel na Linha e quando está
            # visivel ele é requirido.
            for line in self.order_line:
                line.fiscal_operation_id = False

    def _get_invoiceable_lines(self, final=False):
        lines = super()._get_invoiceable_lines(final=final)
        if not self.fiscal_operation_id:
            # O caso Brasil se caracteriza por ter a Operação Fiscal
            return lines
        document_type_id = self._context.get("document_type_id")
        lines_with_fo_line = lines.filtered(lambda ln: ln.fiscal_operation_line_id)
        lines_doc_type = lines_with_fo_line.filtered(
            lambda ln: ln.fiscal_operation_line_id.get_document_type(ln.company_id).id
            == document_type_id
        )
        other_lines = lines.filtered(lambda ln: ln.is_downpayment or ln.display_type)
        lines_doc_type |= other_lines
        return lines_doc_type

    # pylint: disable=except-pass
    def _create_invoices(self, grouped=False, final=False, date=None):
        if not self.fiscal_operation_id:
            return super()._create_invoices(grouped=grouped, final=final, date=date)
        lines_with_fiscal_op_line = self.order_line.filtered(
            lambda ln: ln.fiscal_operation_line_id
        )
        document_types = {
            line.fiscal_operation_line_id.get_document_type(line.company_id)
            for line in lines_with_fiscal_op_line
        }

        moves = self.env["account.move"]
        for document_type in document_types:
            self = self.with_context(document_type_id=document_type.id)
            try:
                moves |= super()._create_invoices(
                    grouped=grouped, final=final, date=date
                )
            except UserError as e:
                if "There is nothing to invoice!" in str(e):
                    # Skip for now, will review later
                    pass
                else:
                    raise

        if not moves and self._context.get("raise_if_nothing_to_invoice", True):
            raise UserError(self._nothing_to_invoice_error_message())

        return moves

    def _prepare_invoice(self):
        self.ensure_one()
        result = super()._prepare_invoice()
        if self.fiscal_operation_id:  # (Brazil)
            fiscal_values = self._prepare_br_fiscal_dict()
            # unlike super()._prepare_invoice(), prepare_fiscal_dict doesn't consider
            # partner_invoice_id, so we adjust the partner_id eventually:
            if fiscal_values.get("partner_id") != result.get("partner_id"):
                fiscal_values["partner_id"] = result.get("partner_id")
            result.update(fiscal_values)

            document_type_id = self._context.get("document_type_id")
            if not document_type_id:
                # Quando ocorre esse caso? Os Testes não estão passando aqui
                document_type_id = self.company_id.document_type_id.id

            document_type = self.env["l10n_br_fiscal.document.type"].browse(
                document_type_id
            )

            if document_type:
                result["document_type_id"] = document_type_id
                document_serie = document_type.get_document_serie(
                    self.company_id, self.fiscal_operation_id
                )
                if document_serie:
                    result["document_serie_id"] = document_serie.id

            if self.fiscal_operation_id.journal_id:
                result["journal_id"] = self.fiscal_operation_id.journal_id.id

        return result

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(
                formatLang,
                self.with_context(lang=order.partner_id.lang).env,
                currency_obj=currency,
            )
            res = {}
            for line in order.order_line:
                taxes = line._compute_taxes(line.fiscal_tax_ids)["taxes"]
                for tax in line.fiscal_tax_ids:
                    computed_tax = taxes.get(tax.tax_domain)
                    pr = order.currency_id.rounding
                    if computed_tax and not float_is_zero(
                        computed_tax.get("tax_value", 0.0), precision_rounding=pr
                    ):
                        group = tax.tax_group_id
                        res.setdefault(group, {"amount": 0.0, "base": 0.0})
                        res[group]["amount"] += computed_tax.get("tax_value", 0.0)
                        res[group]["base"] += computed_tax.get("base", 0.0)
            res = sorted(res.items(), key=lambda line: line[0].sequence)
            order.amount_by_group = [
                (
                    line[0].name,
                    line[1]["amount"],
                    line[1]["base"],
                    fmt(line[1]["amount"]),
                    fmt(line[1]["base"]),
                    len(res),
                )
                for line in res
            ]

    def _get_fiscal_partner(self):
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        # Caso Vendas, a prioridade é do campo informado pelo usuário, quando
        # o Partner tem um contato definido como Tipo Invoice o campo
        # partner_invoice_id é preenchido com esse valor automaticamente
        if partner != self.partner_invoice_id:
            partner = self.partner_invoice_id

        return partner
