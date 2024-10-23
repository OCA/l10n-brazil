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

            # O campo payment_mode_id é implementado com a instalação do
            # l10n_br_account_nfe mas o l10n_br_sale_stock não tem
            # dependencia direta desse modulo, para evitar a necessidade
            # de um 'glue' modulo para resolver isso é feita a verificação
            # se o campo existe antes de preenche-lo
            if hasattr(pick.sale_id, "payment_mode_id"):
                if pick.sale_id.payment_mode_id.id != values.get("payment_mode_id"):
                    values.update({"payment_mode_id": pick.sale_id.payment_mode_id.id})
            if pick.sale_id.incoterm.id != values.get("invoice_incoterm_id"):
                values.update({"invoice_incoterm_id": pick.sale_id.incoterm.id})

            if pick.sale_id.copy_note and pick.sale_id.note:
                # Evita enviar False quando não tem nada
                additional_data = ""
                if pick.sale_id.manual_customer_additional_data:
                    additional_data = f"{pick.sale_id.manual_customer_additional_data}"

                values.update(
                    {
                        "manual_customer_additional_data": additional_data
                        + f" TERMOS E CONDIÇÕES: {pick.sale_id.note}",
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
            # existe um erro a ser resolvido
            # Issue https://github.com/odoo/odoo/issues/77028
            # PR https://github.com/odoo/odoo/pull/77195
            # Além disso é preciso verificar outras questões
            # por exemplo datas de entrega diferentes, informações
            # comerciais que são discriminadas por itens e etc.
            key = key + (move.sale_line_id,)

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
