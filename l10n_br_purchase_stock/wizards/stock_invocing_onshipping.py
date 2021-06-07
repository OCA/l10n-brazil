# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
        if pick.purchase_id:
            values["purchase_id"] = pick.purchase_id.id
            if pick.purchase_id.payment_term_id.id != values["payment_term_id"]:
                values.update({"payment_term_id": pick.purchase_id.payment_term_id.id})

        return invoice, values

    def _get_move_key(self, move):
        """
        Get the key based on the given move
        :param move: stock.move recordset
        :return: key
        """
        key = super()._get_move_key(move)
        if move.purchase_line_id:
            # TODO: deveria permitir agrupar as linhas ?
            #  Deveria permitir agrupar Pedidos de Compras ?
            if type(key) is tuple:
                key = key + (move.purchase_line_id,)
            else:
                # TODO - seria melhor identificar o TYPE para saber se
                #  o KEY realmente é um objeto nesse caso
                key = (key, move.purchase_line_id)

        return key

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """

        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        # Devido ao KEY com purchase_line_id aqui
        # vem somente um registro
        if len(moves) == 1:
            # Caso venha apenas uma linha porem sem
            # purchase_line_id é preciso ignora-la
            if moves.purchase_line_id:
                values["purchase_line_id"] = moves.purchase_line_id.id

        return values
