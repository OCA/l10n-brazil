# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    fiscal_operation_journal = fields.Boolean(
        string="Account Jornal from Fiscal Operation",
        default=True,
    )

    group = fields.Selection(
        selection_add=[("fiscal_operation", "Fiscal Operation")],
        ondelete={"fiscal_operation": "set default"},
    )

    def _get_journal(self):
        """
        Get the journal depending on the journal_type
        :return: account.journal recordset
        """
        self.ensure_one()
        if self.fiscal_operation_journal:
            pickings = self._load_pickings()
            picking = fields.first(pickings)
            journal = picking.fiscal_operation_id.journal_id
            if not journal:
                raise UserError(
                    _(
                        "Invalid Journal! There is not journal defined"
                        " for this company: %s in fiscal operation: %s !"
                    )
                    % (picking.company_id.name, picking.fiscal_operation_id.name)
                )
        else:
            journal = super()._get_journal()

        return journal

    def _build_invoice_values_from_pickings(self, pickings):
        invoice, values = super()._build_invoice_values_from_pickings(pickings)
        pick = fields.first(pickings)
        fiscal_vals = pick._prepare_br_fiscal_dict()

        document_type = pick.company_id.document_type_id
        document_type_id = pick.company_id.document_type_id.id

        fiscal_vals["document_type_id"] = document_type_id

        document_serie = document_type.get_document_serie(
            pick.company_id, pick.fiscal_operation_id
        )
        if document_serie:
            fiscal_vals["document_serie_id"] = document_serie.id

        if pick.fiscal_operation_id and pick.fiscal_operation_id.journal_id:
            fiscal_vals["journal_id"] = pick.fiscal_operation_id.journal_id.id

        # Endereço de Entrega diferente do Endereço de Faturamento
        # so informado quando é diferente
        if fiscal_vals["partner_id"] != values["partner_id"]:
            values["partner_shipping_id"] = fiscal_vals["partner_id"]
        else:
            # Já no modulo stock_picking_invoicing o campo partner_shipping_id
            # é informado mas para evitar ter a NFe com o Endereço de Entrega
            # quando esse é o mesmo Endereço, esta sendo removido.
            # TODO: Deveria ser informado mesmo quando é o mesmo? Isso não
            #  acontecia na v12.
            del values["partner_shipping_id"]

        # Ser for feito o update como abaixo o campo
        # fiscal_operation_id vai vazio
        # fiscal_vals.update(values)
        values.update(fiscal_vals)

        return invoice, values

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """

        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        move = fields.first(moves)
        fiscal_values = move._prepare_br_fiscal_dict()

        # A Fatura não pode ser criada com os campos price_unit e fiscal_price
        # negativos, o metodo _prepare_br_fiscal_dict retorna o price_unit
        # negativo, por isso é preciso tira-lo antes do update, e no caso do
        # fiscal_price é feito um update para caso do valor ser diferente do
        # price_unit
        del fiscal_values["price_unit"]
        fiscal_values["fiscal_price"] = abs(fiscal_values.get("fiscal_price"))

        # Como é usada apenas uma move para chamar o _prepare_br_fiscal_dict
        # a quantidade/quantity do dicionario traz a quantidade referente a
        # apenas a essa linha por isso é removido aqui.
        del fiscal_values["quantity"]

        # Mesmo a quantidade estando errada por ser chamada apenas por uma move
        # no caso das stock.move agrupadas e os valores fiscais e de totais
        # retornados poderem estar errados ao criar o documento fiscal isso
        # será recalculado já com a quantidade correta.

        values.update(fiscal_values)

        values["tax_ids"] = [
            (
                6,
                0,
                self.env["l10n_br_fiscal.tax"]
                .browse(fiscal_values["fiscal_tax_ids"])
                .account_taxes()
                .ids,
            )
        ]

        return values

    def _get_move_key(self, move):
        """
        Get the key based on the given move
        :param move: stock.move recordset
        :return: key
        """
        key = super()._get_move_key(move)
        if move.fiscal_operation_line_id:
            # Linhas de Operações Fiscais diferentes
            # não podem ser agrupadas
            key = key + (move.fiscal_operation_line_id,)

        return key
