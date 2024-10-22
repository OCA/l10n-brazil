# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

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
