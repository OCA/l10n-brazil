# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2022  Renan Hiroki Bastos - Kmee
# Copyright (C) 2023  Luiz Felipe do Divino - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class NfeImport(models.TransientModel):
    _inherit = "l10n_br_nfe.import_xml"

    model_to_link = fields.Selection(
        string="Link with",
        selection=[("picking", "Picking"), ("purchase", "Purchase Order")],
        required=True,
    )

    link_type = fields.Selection(
        selection=[
            ("choose", "Choose"),
            ("create", "Create"),
        ],
        string="Link Type",
        default="create",
        required=True,
    )

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
    )

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Picking",
    )

    has_error = fields.Boolean()

    error_message = fields.Text()

    @api.onchange("xml_partner_cpf_cnpj")
    def _onchange_partner_cpf_cnpj(self):
        if not self.xml_partner_cpf_cnpj:
            return

        purchase_order_ids = self._get_purchase_orders_from_xml_supplier()
        picking_ids = self._get_pickings_from_xml_supplier()
        return {
            "domain": {
                "purchase_id": [("id", "in", purchase_order_ids.ids)],
                "picking_id": [("id", "in", picking_ids.ids)],
            }
        }

    @api.depends("model_to_link")
    def _onchange_model_to_link(self):
        self.purchase_id = False
        self.picking_id = False
        self.has_error = False
        self.error_message = ""

    @api.depends("link_type")
    def _onchange_link_type(self):
        self.has_error = False
        self.error_message = ""
        if self.link_type == "create":
            self.purchase_id = False
            self.picking_id = False

    @api.onchange(
        "purchase_id",
        "imported_products_ids.uom_conversion_factor",
        "imported_products_ids.product_id",
    )
    def _onchange_purchase_id(self):
        self.has_error = False
        self.error_message = ""

        if self.model_to_link == "purchase" and self.purchase_id:
            purchase_products = self.purchase_id.order_line.mapped("product_id")
            document_products = self.imported_products_ids.mapped("product_id")
            if purchase_products != document_products:
                self.has_error = True
                self.error_message += _(
                    "Purchase Order products don't match imported document products."
                )
                return

            for line in self.purchase_id.order_line:
                imported_product_id = self.imported_products_ids.filtered(
                    lambda s: s.product_id == line.product_id
                )
                if (
                    imported_product_id
                    and imported_product_id.quantity_com
                    != line.product_qty * imported_product_id.uom_conversion_factor
                ):
                    self.has_error = True
                    if self.error_message:
                        self.error_message += "\n\n"
                    self.error_message += _(
                        "%s: Purchase Order quantity does not match imported document quantity."
                        % line.product_id.name
                    )

                if (
                    imported_product_id
                    and imported_product_id.price_unit_com != line.price_unit
                ):
                    self.has_error = True
                    if self.error_message:
                        self.error_message += "\n\n"
                    self.error_message += _(
                        "%s: Purchase Order price does not match imported document price. "
                        "The price in the Purchase Order will be overwriten."
                        % line.product_id.name
                    )

    @api.onchange(
        "picking_id",
        "imported_products_ids.uom_conversion_factor",
        "imported_products_ids.product_id",
    )
    def _onchange_picking_id(self):
        self.has_error = False
        self.error_message = ""

        if self.model_to_link == "picking" and self.picking_id:
            picking_products = self.picking_id.move_ids_without_package.mapped(
                "product_id"
            )
            document_products = self.imported_products_ids.mapped("product_id")
            if picking_products != document_products:
                self.has_error = True
                self.error_message += _(
                    "Picking products don't match imported document products."
                )
                return

            for line in self.picking_id.move_ids_without_package:
                imported_product_id = self.imported_products_ids.filtered(
                    lambda s: s.product_id == line.product_id
                )
                if (
                    imported_product_id
                    and imported_product_id.quantity_com
                    != line.product_uom_qty * imported_product_id.uom_conversion_factor
                ):
                    self.has_error = True
                    if self.error_message:
                        self.error_message += "\n\n"
                    self.error_message += _(
                        "%s: Picking quantity does not match imported document quantity."
                        % (line.product_id.name)
                    )

    def _get_purchase_orders_from_xml_supplier(self):
        supplier_id = self.env["res.partner"].search(
            [("cnpj_cpf", "=", self.xml_partner_cpf_cnpj)]
        )
        return self.env["purchase.order"].search(
            [
                ("partner_id", "=", supplier_id.id),
                ("state", "not in", ["done", "cancel"]),
            ]
        )

    def _get_pickings_from_xml_supplier(self):
        supplier_id = self.env["res.partner"].search(
            [("cnpj_cpf", "=", self.xml_partner_cpf_cnpj)]
        )
        return self.env["stock.picking"].search(
            [
                ("partner_id", "=", supplier_id.id),
                ("state", "not in", ["done", "cancel"]),
            ]
        )

    def _create_edoc_from_xml(self):
        edoc = super(NfeImport, self)._create_edoc_from_xml()

        if self.model_to_link == "purchase":
            if self.link_type == "create":
                self.purchase_id = self._create_purchase_order(edoc)
                self.purchase_id.button_confirm()
                self._update_purchase_order()
            elif self.purchase_id and self.link_type == "choose":
                self.purchase_id.button_confirm()
                self._update_purchase_order()
            else:
                raise UserError(_("No Purchase Order Selected."))
            edoc.linked_purchase_ids = [(4, self.purchase_id.id)]
            if edoc.move_ids:
                self._add_invoice_to_purchase(edoc)
        elif self.model_to_link == "picking":
            if self.link_type == "create":
                self.picking_id = self._create_picking(edoc)
                self.picking_id.action_confirm()
            elif self.picking_id and self.link_type == "choose":
                self._update_picking()
            else:
                raise UserError(_("No Picking Selected."))
            edoc.linked_picking_ids = [(4, self.picking_id.id)]
            if edoc.move_ids:
                self._add_invoice_to_picking(edoc)

        return edoc

    def _create_purchase_order(self, document):
        purchase = self.env["purchase.order"].create(
            {
                "partner_id": document.partner_id.id,
                "currency_id": self.company_id.currency_id.id,
                "fiscal_operation_id": self._get_purchase_fiscal_operation_id(),
                "date_order": datetime.now(),
                "origin_document_id": document.id,
                "imported": True,
            }
        )

        purchase_lines = []
        for line in document.fiscal_line_ids:
            imported_product_id = self.imported_products_ids.filtered(
                lambda p: p.product_id == line.product_id
            )

            purchase_line = self.env["purchase.order.line"].create(
                {
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name,
                    "date_planned": datetime.now(),
                    "product_qty": line.quantity,
                    "product_uom": line.uom_id.id or line.product_id.uom_id.id,
                    "partner_uom_factor": imported_product_id.uom_conversion_factor,
                    "price_unit": line.price_unit,
                    "price_subtotal": line.amount_total,
                    "order_id": purchase.id,
                }
            )
            purchase_lines.append(purchase_line.id)
        purchase.write({"order_line": [(6, 0, purchase_lines)]})
        return purchase

    def _create_picking(self, document):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": document.partner_id.id,
                "currency_id": self.company_id.currency_id.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "fiscal_operation_id": self._get_picking_fiscal_operation_id(),
                "scheduled_date": datetime.now(),
                "date_done": datetime.now(),
                "location_dest_id": self.env.ref(
                    "stock.picking_type_in"
                ).default_location_dest_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "origin_document_id": document.id,
                "imported": True,
            }
        )

        stock_moves = []
        for line in document.fiscal_line_ids:
            imported_product_id = self.imported_products_ids.filtered(
                lambda p: p.product_id == line.product_id
            )
            conversion_factor = imported_product_id.uom_conversion_factor

            stock_move = self.env["stock.move"].create(
                {
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name,
                    "product_uom_qty": line.quantity * conversion_factor,
                    "quantity_done": line.quantity * conversion_factor,
                    "fiscal_quantity": line.quantity * conversion_factor,
                    "product_uom": line.product_id.uom_id.id,
                    "price_unit": line.price_unit,
                    "invoice_state": "none",
                    "picking_type_id": self.env.ref("stock.picking_type_in").id,
                    "location_dest_id": self.env.ref(
                        "stock.picking_type_in"
                    ).default_location_dest_id.id,
                    "location_id": self.env.ref("stock.stock_location_suppliers").id,
                    "picking_id": picking.id,
                }
            )
            stock_moves.append(stock_move.id)
        picking.write({"move_ids_without_package": [(6, 0, stock_moves)]})
        return picking

    def _get_purchase_fiscal_operation_id(self):
        default_fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras").id
        return (
            self.env.user.company_id.purchase_fiscal_operation_id.id
            or default_fiscal_operation_id
        )

    def _get_picking_fiscal_operation_id(self):
        default_fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras").id
        return (
            self.env.user.company_id.stock_in_fiscal_operation_id.id
            or default_fiscal_operation_id
        )

    def _update_purchase_order(self):
        self.picking_id = self.purchase_id.picking_ids.filtered(
            lambda p: p.state not in ["done", "cancel"]
        )
        self._update_picking()

    def _update_picking(self):
        for line in self.picking_id.move_ids_without_package:
            imported_product_ids = self.imported_products_ids.filtered(
                lambda s: s.product_id == line.product_id
            )
            if not imported_product_ids:
                continue
            quantity_done = 0
            for imported_line in imported_product_ids:
                quantity_done += (
                    imported_line.quantity_com * imported_line.uom_conversion_factor
                )
            line.quantity_done = quantity_done

    def _add_invoice_to_purchase(self, edoc):
        for order_line in self.purchase_id.order_line:
            invoice_line_ids = edoc.move_ids.mapped("line_ids").filtered(
                lambda il: il.product_id == order_line.product_id
            )
            order_line.write(
                {
                    "invoice_lines": [(6, 0, invoice_line_ids.ids)],
                }
            )
        self._add_invoice_to_picking(edoc)

    def _add_invoice_to_picking(self, edoc):
        edoc.move_ids.write(
            {
                "picking_ids": [(4, self.picking_id.id)],
            }
        )
        self.picking_id._set_as_invoiced()
