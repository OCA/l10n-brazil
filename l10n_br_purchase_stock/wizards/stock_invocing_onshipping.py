# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_PARTNER


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
            values["issuer"] = DOCUMENT_ISSUER_PARTNER

            if pick.purchase_id.payment_term_id.id != values.get(
                "invoice_payment_term_id"
            ):
                values.update(
                    {"invoice_payment_term_id": pick.purchase_id.payment_term_id.id}
                )

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
            key = key + (move.purchase_line_id,)

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
                values[
                    "analytic_account_id"
                ] = moves.purchase_line_id.account_analytic_id.id
                values["analytic_tag_ids"] = [
                    (6, 0, moves.purchase_line_id.analytic_tag_ids.ids)
                ]

        return values
