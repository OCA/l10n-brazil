# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


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
        values["sale_line_ids"] = [(6, 0, sale_line_id.ids)]
        sale_line_id = moves.sale_line_id
        analytic_account_id = sale_line_id.order_id.analytic_account_id.id
        if sale_line_id.analytic_distribution and not sale_line_id.display_type:
            values["analytic_distribution"] = sale_line_id.analytic_distribution
        if analytic_account_id and not sale_line_id.display_type:
            analytic_account_id = str(analytic_account_id)
            if "analytic_distribution" in values:
                values["analytic_distribution"][analytic_account_id] = (
                    values["analytic_distribution"].get(analytic_account_id, 0) + 100
                )
            else:
                values["analytic_distribution"] = {analytic_account_id: 100}

        return values
