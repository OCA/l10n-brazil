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
            values.update(
                {
                    "partner_id": pick.sale_id.partner_invoice_id.id,
                }
            )

            if pick.sale_id.payment_term_id.id != values.get("invoice_payment_term_id"):
                values.update(
                    {"invoice_payment_term_id": pick.sale_id.payment_term_id.id}
                )
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

    def _get_move_key(self, move):
        """
        Get the key based on the given move
        :param move: stock.move recordset
        :return: key
        """
        key = super()._get_move_key(move)
        if move.sale_line_id:
            # Apesar da linha da Fatura permitir ter mais de uma linha de
            # pedido de venda associada(campo sale_line_ids na invoice line)
            # por enquanto esta sendo separado já que tem questões a serem
            # verificadas por exemplo datas de entrega diferentes, informações
            # comerciais que são discriminadas por itens e etc.
            # TODO - verificar se poderia ser feito, é preciso incluir
            #  dados de demontração e testes com casos de uso para confirmar
            if type(key) is tuple:
                key = key + (move.sale_line_id,)
            else:
                # TODO - seria melhor identificar o TYPE para saber se
                #  o KEY realmente é um objeto nesse caso
                key = (key, move.sale_line_id)

        return key

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
        if len(moves) == 1:
            # Caso venha apenas uma linha porem sem
            # sale_line_id é preciso ignora-la
            if moves.sale_line_id:
                values["sale_line_ids"] = [(6, 0, moves.sale_line_id.ids)]

        return values
