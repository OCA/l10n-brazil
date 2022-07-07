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
            if pick.sale_id.payment_term_id.id != values["payment_term_id"]:
                values.update({"payment_term_id": pick.sale_id.payment_term_id.id})
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
                # TODO - Outros modulos podem sobre escrever o metodo
                #  _prepare_invoice_line do objeto sale_order_line
                #  para incluir novos campos ex.: modulo sale_commission
                #  inclui a comissão e isso funciona quando a Fatura
                #  account.invoice é criada a partir do sale.order,
                #  mas quando é criada a partir do stock.picking
                #  essa informação não existe é sem o código abaixo
                #  a account.invoice é criada sem essa informação,
                #  provavelmente existe uma forma melhor de resolver.

                # Campos comuns das linhas do Pedido de Vendas
                # e as linhas da Fatura/Invoice.
                sol_fields = [key for key in self.env["sale.order.line"]._fields.keys()]

                acl_fields = [
                    key for key in self.env["account.invoice.line"]._fields.keys()
                ]

                # Campos que devem ser desconsiderados
                skipped_fields = [
                    "id",
                    "display_name",
                    "state",
                    "create_date",
                    "product_image",
                    "create_uid",
                    "write_uid",
                    "price_subtotal",
                    "write_date",
                    "price_total",
                    "__last_update",
                    "amount_total",
                    "amount_fiscal",
                    "financial_total",
                    "name",
                    "display_type",
                    # Caso de endereço De Entrega diferente do De Faturamento
                    "partner_id",
                    # TODO deveria estar aqui?
                    # values_prepare_inv_line
                    #  campo        | valor stock.move |  valor prepare_invoice_line
                    #  fiscal_price |     100.0        |  500.0
                    "fiscal_price",
                    #  campo        | valor stock.move |  valor prepare_invoice_line
                    #  amount_taxed |     -200.0       |  1000.0
                    "amount_taxed",
                    #  campo        | valor stock.move |  valor prepare_invoice_line
                    #  amount_untaxed |     -200.0       |  1000.0
                    "amount_untaxed",
                    "financial_total_gross",
                    # price_gross -200.0 <class 'float'> 1000.0
                    "price_gross",
                    # Evitar o caso de Devolução/Refund onde os campos
                    # não são iguais
                    "ipi_cst_code",
                    "cofins_cst_id",
                    "cfop_id",
                    "pis_cst_code",
                    "fiscal_operation_line_id",
                    "fiscal_operation_id",
                    "pis_cst_id",
                    "fiscal_operation_type",
                    "icms_origin",
                ]

                common_fields = list(
                    set(acl_fields) & set(sol_fields) - set(skipped_fields)
                )
                values_prepare_inv_line = moves.sale_line_id._prepare_invoice_line(
                    moves.product_qty
                )
                for field in common_fields:

                    # Verifica os casos em que não há nada a fazer
                    if not values_prepare_inv_line.get(field):
                        continue
                    elif type(values_prepare_inv_line.get(field)) is list:
                        if not values_prepare_inv_line.get(field)[0][2]:
                            # Exemplo Lista vazia [(6, 0, [])]
                            continue
                    elif self._get_invoice_type() == "out_refund":
                        # Caso de Devolução os valores não são iguais
                        # TODO Deveria chamar algum metodo?
                        continue

                    # Verifica os casos de diferenças
                    # entre os valores nos dicionarios
                    if not values.get(field) and values_prepare_inv_line.get(field):
                        # Campo está vazio no values mas não no _prepare_invoice_line
                        values[field] = values_prepare_inv_line.get(field)

                    elif (
                        values.get(field)
                        and type(values_prepare_inv_line.get(field)) is list
                    ):
                        # O campo tem valor mas é uma lista vazia
                        if (
                            values[field][0][2]
                            != values_prepare_inv_line.get(field)[0][2]
                        ):
                            # Caso lista vazia mas tem valor
                            # no _prepare_invoice_line exemplo:
                            # field =>agents
                            # values.get(field) =>[(6, 0, [])]
                            # values_prepare_inv_line.get(field) =>
                            # [(0, 0, {'agent': 75, 'commission': 1})]
                            values[field] = values_prepare_inv_line.get(field)

                    elif values.get(field) != values_prepare_inv_line.get(field):
                        # Valor do campo é diferente do valor do _prepare_invoice_line
                        values[field] = values_prepare_inv_line.get(field)

                # Associção entre a Fatura é o Pedido de Venda
                values["sale_line_ids"] = [(6, 0, moves.sale_line_id.ids)]

        return values
