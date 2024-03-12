# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _build_invoice_values_from_pickings(self, pickings):
        """
        Build dict to create a new invoice from given pickings
        :param pickings: stock.picking recordset
        :return: dict
        """
        invoice, values = super()._build_invoice_values_from_pickings(pickings)

        pick = fields.first(pickings)
        if pick.sale_id:
            # O campo payment_mode_id é implementado com a instalação do
            # l10n_br_account_nfe mas o l10n_br_sale_stock não tem
            # dependencia direta desse modulo, para evitar a necessidade
            # de um 'glue' modulo para resolver isso é feita a verificação
            # se o campo existe antes de preenche-lo
            if hasattr(pick.sale_id, "payment_mode_id"):
                if pick.sale_id.payment_mode_id.id != values.get("payment_mode_id"):
                    values.update({"payment_mode_id": pick.sale_id.payment_mode_id.id})

            if pick.sale_id.copy_note and pick.sale_id.note:
                # Evita enviar False quando não tem nada
                additional_data = ""
                if pick.sale_id.manual_customer_additional_data:
                    additional_data = "{}".format(
                        pick.sale_id.manual_customer_additional_data
                    )

                values.update(
                    {
                        "manual_customer_additional_data": additional_data
                        + " TERMOS E CONDIÇÕES: {}".format(pick.sale_id.note),
                    }
                )

        return invoice, values
