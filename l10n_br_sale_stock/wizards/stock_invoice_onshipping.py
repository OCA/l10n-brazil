# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, models
from odoo.tools import float_compare


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
            # the others will be overwritting, as done in sale module,
            # one more field include here Note
            customer_data = set()
            fiscal_data = set()
            for picking in sale_pickings:
                # TODO: Avaliar se isso deveria ser feito no l10n_br_sale,
                #  porque dessa forma evitaria a necessidade de ser feito aqui
                picking.sale_id._prepare_invoice()
                # Fields to Join
                # Evita enviar False quando não tem nada
                # {False}     {''}
                additional_data = ""
                if picking.sale_id.manual_customer_additional_data:
                    additional_data = "{}".format(
                        picking.sale_id.manual_customer_additional_data
                    )
                customer_data.add(additional_data)
                values["manual_customer_additional_data"] = additional_data

                # Evita enviar False quando não tem nada
                fiscal_additional_data = ""
                if picking.sale_id.manual_fiscal_additional_data:
                    fiscal_additional_data = "{}".format(
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

    def _update_fiscal_values_from_sale_line(self, moves, values):
        """The values from the sale line are prepared on its quantity to
        invoice, which is still zero for products invoiced on delivery when
        the picking is not done yet. Prepare them again on the quantity
        being invoiced, so the fiscal values match the invoice line."""
        sale_line = moves.sale_line_id
        if (
            len(sale_line) != 1
            or sale_line.display_type
            or self._get_invoice_type() == "out_refund"
            or "quantity" not in values
        ):
            return
        quantity = values["quantity"]
        uom = self.env["uom.uom"].browse(values.get("product_uom_id"))
        if uom and uom != sale_line.product_uom:
            quantity = uom._compute_quantity(quantity, sale_line.product_uom)
        if not float_compare(
            quantity,
            sale_line.qty_to_invoice,
            precision_rounding=sale_line.product_uom.rounding,
        ):
            return
        sale_line_values = sale_line._prepare_invoice_line(quantity=quantity)
        fields_not_used = self._get_fields_not_used_from_sale_line()
        values.update(
            {
                fname: value
                for fname, value in sale_line_values.items()
                if fname not in fields_not_used
            }
        )

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """

        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        self._update_fiscal_values_from_sale_line(moves, values)
        # Devido ao KEY com sale_line_id aqui
        # vem somente um registro
        # Caso venha apenas uma linha porem sem
        # sale_line_id é preciso ignora-la
        if len(moves) != 1 or not moves.sale_line_id:
            return values

        sale_line_id = moves.sale_line_id
        values["sale_line_ids"] = [Command.set(sale_line_id.ids)]
        sale_line_id = moves.sale_line_id
        analytic_account_id = sale_line_id.order_id.analytic_account_id.id
        if sale_line_id.analytic_distribution and not sale_line_id.display_type:
            values["analytic_distribution"] = sale_line_id.analytic_distribution
        if analytic_account_id and not sale_line_id.display_type:
            analytic_account_id = str(analytic_account_id)
            distribution = values.get("analytic_distribution") or {}
            if analytic_account_id not in distribution:
                distribution[analytic_account_id] = 100
            values["analytic_distribution"] = distribution

        return values
