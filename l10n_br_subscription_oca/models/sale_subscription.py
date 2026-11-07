# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleSubscription(models.Model):
    _name = "sale.subscription"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.sale_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        return [
            ("fiscal_operation_type", "=", "out"),
            ("state", "=", "approved"),
            ("fiscal_type", "not ilike", "%refund%"),
        ]

    company_country_id = fields.Many2one(related="company_id.country_id")

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_subscription_comment_rel",
        column1="subscription_id",
        column2="comment_id",
        string="Comments",
    )

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "sale_subscription_line_ids"

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form" and self.env.company.country_id.code == "BR":
            arch = self.env["sale.subscription.line"].inject_fiscal_fields(arch)
            if self.user_has_groups("l10n_br_sale.group_line_fiscal_detail"):
                for tree in arch.xpath(
                    "//field[@name='sale_subscription_line_ids']/tree"
                ):
                    tree.attrib["editable"] = ""
        return arch, view

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id.fiscal_position_id:
            self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

    def _get_document_type(self):
        """Fiscal document type of the invoice, taken from the lines.

        subscription_oca creates a single invoice per subscription, so all
        its lines must share the same fiscal document type.
        """
        self.ensure_one()
        document_types = self.env["l10n_br_fiscal.document.type"]
        for line in self.sale_subscription_line_ids.filtered(
            "fiscal_operation_line_id"
        ):
            document_types |= line.fiscal_operation_line_id.get_document_type(
                self.company_id
            )
        if len(document_types) > 1:
            raise UserError(
                _(
                    "The lines of subscription %(name)s need different fiscal "
                    "documents (%(types)s). Split them into one subscription "
                    "per fiscal document type.",
                    name=self.name,
                    types=", ".join(document_types.mapped("name")),
                )
            )
        return document_types or self.company_id.document_type_id

    def _prepare_account_move(self, line_ids):
        values = super()._prepare_account_move(line_ids)
        if not self.fiscal_operation_id:
            return values
        values.update(self._prepare_br_fiscal_dict())
        document_type = self._get_document_type()
        if document_type:
            values["document_type_id"] = document_type.id
            document_serie = document_type.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if document_serie:
                values["document_serie_id"] = document_serie.id
        if self.fiscal_operation_id.journal_id:
            values["journal_id"] = self.fiscal_operation_id.journal_id.id
        return values

    def _prepare_sale_order(self, line_ids=False):
        values = super()._prepare_sale_order(line_ids)
        values["fiscal_operation_id"] = self.fiscal_operation_id.id
        return values
