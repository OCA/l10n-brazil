# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _fiscal_operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain=lambda self: self._fiscal_operation_domain(),
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="stock_picking_comment_rel",
        column1="picking_id",
        column2="comment_id",
        string="Comments",
        compute="_compute_comment_ids",
        store=True,
    )

    currency_id = fields.Many2one(
        default=lambda self: self.env.company.currency_id,
    )

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "move_ids"

    @api.depends("move_ids.price_unit")
    def _amount_all(self):
        """Compute the total amounts of the Picking."""
        for picking in self:
            picking._compute_fiscal_amount()

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_id.code == "BR":
            arch = self.env["stock.move"].inject_fiscal_fields(arch)

        return arch, view

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        package = super()._put_in_pack(move_line_ids, create_package_level)
        if (
            package
            and self.picking_type_id.pre_generate_fiscal_document_number == "pack"
        ):
            self._generate_document_number()
        return package

    def button_validate(self):
        result = super().button_validate()
        for record in self:
            if (
                record.state == "done"
                and record.picking_type_id.pre_generate_fiscal_document_number
                == "validate"
            ):
                record._generate_document_number()
        return result

    def _generate_document_number(self):
        if self.company_id.document_type_id and self.fiscal_operation_id:
            if self.document_serie and self.document_number:
                return
            self.document_type_id = self.company_id.document_type_id
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            self.document_serie = self.document_serie_id.code
            self.document_number = self.document_serie_id.next_seq_number()

    def _get_fiscal_partner(self):
        """
        Adjust the partner, both for an invoice from picking with
        no related SO or PO,
        https://github.com/OCA/account-invoicing/blob/14.0/
        stock_picking_invoicing/models/stock_picking.py#L38
        and also in the case of a picking originating from a PO:
        https://github.com/OCA/OCB/blob/14.0/addons/purchase/
        models/purchase.py#L556
        """
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        if partner.id != partner.address_get(["invoice"]).get("invoice"):
            partner = self.env["res.partner"].browse(
                partner.address_get(["invoice"]).get("invoice")
            )
        return partner

    def _get_default_fiscal_operation(self):
        """
        Meant to be overriden in modules such as
        l10n_br_sale_stock
        l10n_br_purchase_stock
        """
        if self.env.company.country_id.code == "BR":
            fiscal_operation = self.env.company.stock_fiscal_operation_id
            picking_type_id = self.picking_type_id.id
            if not picking_type_id:
                # Quando isso é necessário? Testes não passam aqui,
                # dependendo ver de remover
                picking_type_id = self.env.context.get("default_picking_type_id")
            if picking_type_id:
                picking_type = self.env["stock.picking.type"].browse(picking_type_id)
                fiscal_operation = picking_type.fiscal_operation_id or (
                    self.env.company.stock_in_fiscal_operation_id
                    if picking_type.code == "incoming"
                    else self.env.company.stock_out_fiscal_operation_id
                )

            return fiscal_operation

    @api.onchange("invoice_state")
    def _onchange_invoice_state(self):
        result = super()._onchange_invoice_state()
        for record in self:
            fiscal_operation = record._get_default_fiscal_operation()
            if fiscal_operation:
                record.fiscal_operation_id = fiscal_operation
        return result

    def set_to_be_invoiced(self):
        """
        Update invoice_state of current pickings to "2binvoiced".
        :return: dict
        """
        # Necessário para preencher a OP Fiscal Padrão quando
        # ao inves de selecionar o invoice_state pelo campo
        # é feito pelo botão
        self._onchange_invoice_state()

        return super().set_to_be_invoiced()
