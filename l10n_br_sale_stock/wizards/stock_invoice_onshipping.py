# Copyright 2020 KMEE
# Copyright (C) 2021  Magno Costa - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _get_fields_not_used_from_sale(self):
        """Fields not used from Sale 'prepare' method"""
        fields_not_used = super()._get_fields_not_used_from_sale()
        fields_not_used.update(
            {
                "document_number",
                "document_serie",
            }
        )
        return fields_not_used

    def _build_invoice_values_from_pickings(self, pickings):
        """
        Build dict to create a new invoice from given pickings
        :param pickings: stock.picking recordset
        :return: dict
        """
        invoice, values = super()._build_invoice_values_from_pickings(pickings)

        sale_pickings = pickings.filtered(lambda pk: pk.sale_id)

        # Refund case don't get values from Sale Dict
        # TODO: Should get any value?
        if sale_pickings and self._get_invoice_type() != "out_refund":
            # Case more than one Sale Order the fields below will be join
            # the others will be overwriting, as done in sale module,
            # one more field include here Note
            customer_data = set()
            fiscal_data = set()
            for picking in sale_pickings:
                # TODO: Avaliar se isso deveria ser feito no l10n_br_sale,
                #  porque dessa forma evitaria a necessidade de ser feito aqui
                picking.sale_id._prepare_invoice()
                # Fields to Join
                additional_data = ""
                if picking.sale_id.manual_customer_additional_data:
                    additional_data = str(
                        picking.sale_id.manual_customer_additional_data
                    )
                customer_data.add(additional_data)
                values["manual_customer_additional_data"] = additional_data

                fiscal_additional_data = ""
                if picking.sale_id.manual_fiscal_additional_data:
                    fiscal_additional_data = str(
                        picking.sale_id.manual_fiscal_additional_data
                    )
                fiscal_data.add(fiscal_additional_data)
                values["manual_fiscal_additional_data"] = fiscal_additional_data

            # Fields to join
            if len(sale_pickings) > 1:
                values.update(
                    {
                        "manual_customer_additional_data": ", ".join(customer_data),
                        "manual_fiscal_additional_data": ", ".join(fiscal_data),
                    }
                )

        return invoice, values

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        # Devido ao KEY com sale_line_id aqui
        # vem somente um registro
        # Caso venha apenas uma linha porem sem
        # sale_line_id é preciso ignora-la
        if len(moves) != 1 or not moves.sale_line_id:
            return values

        sale_line_id = moves.sale_line_id
        values["sale_line_ids"] = [Command.set(sale_line_id.ids)]
        if sale_line_id.analytic_distribution and not sale_line_id.display_type:
            values["analytic_distribution"] = dict(sale_line_id.analytic_distribution)

        if moves.fiscal_operation_id and moves.product_id != sale_line_id.product_id:
            values.update(self._get_kit_component_fiscal_values(moves, values))

        return values

    def _get_kit_component_fiscal_values(self, move, values):
        """Fiscal values of a component move of a phantom kit.

        The component moves of a kit all point to the sale line of the kit,
        so the fiscal values taken from that line (fiscal price and quantity,
        discount, freight, NCM, taxes...) belong to the whole kit and not to
        the component: the NF-e is rejected (630: vProd differs from
        vUnTrib x qTrib) and the discount is applied once per component.

        The fiscal values are recomputed for the component product, quantity
        and price, and the amounts of the sale line are prorated over the
        components by their share of the invoiced price, the rounding
        difference going to the last component.
        """
        mixin_fields = self.env["l10n_br_fiscal.document.line.mixin"]._fields
        product_fields = self._get_kit_component_recomputed_fields()
        fiscal_values = {
            fname: value
            for fname, value in values.items()
            if fname in mixin_fields and fname not in product_fields
        }
        virtual = self.env["l10n_br_fiscal.document.line"].new(fiscal_values)
        virtual.product_id = move.product_id
        virtual.quantity = values.get("quantity", move.quantity)
        virtual.price_unit = values.get("price_unit", 0.0)
        virtual.update(self._get_kit_component_prorated_amounts(move))
        recomputed = (
            set(fiscal_values)
            | (product_fields & set(virtual._fields))
            | set(self._get_kit_component_prorated_fields())
        ) - {"product_id", "price_unit", "quantity"}
        return {
            fname: virtual._fields[fname].convert_to_write(virtual[fname], virtual)
            for fname in recomputed
        }

    def _get_kit_component_recomputed_fields(self):
        """Fields of the kit sale line that depend on the product sold, and
        must be recomputed for the component product."""
        return {
            "product_id",
            "fiscal_price",
            "fiscal_quantity",
            "uot_id",
            "ncm_id",
            "cest_id",
            "nbm_id",
            "nbs_id",
            "icms_origin",
            "fiscal_genre_id",
            "fiscal_type",
            "service_type_id",
            "tax_icms_or_issqn",
        }

    def _get_kit_component_prorated_fields(self):
        """Amounts of the kit sale line to prorate over its components."""
        return ("discount_value", "freight_value", "insurance_value", "other_value")

    def _get_kit_component_prorated_amounts(self, move):
        sale_line = move.sale_line_id
        components = sale_line.move_ids.filtered(
            lambda m: m.state != "cancel" and m.product_id != sale_line.product_id
        ).sorted("id")
        inv_type = self._get_invoice_type()
        weights = {
            component: component._get_price_unit_invoice(
                inv_type, component.picking_id.partner_id
            )
            * (component.quantity or component.product_uom_qty)
            for component in components
        }
        total_weight = sum(weights.values())
        currency = sale_line.currency_id
        amounts = {}
        for fname in self._get_kit_component_prorated_fields():
            total = sale_line[fname]
            if not total or not total_weight:
                amounts[fname] = 0.0 if not total else total / (len(components) or 1)
                continue
            shares = {
                component: currency.round(total * weight / total_weight)
                for component, weight in weights.items()
            }
            last = components[-1:]
            shares[last] = currency.round(total - sum(shares.values()) + shares[last])
            amounts[fname] = shares.get(move, 0.0)
        return amounts
