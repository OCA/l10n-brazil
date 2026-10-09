# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _l10n_br_rental_pickings(self):
        return self._load_pickings().filtered("picking_type_id.l10n_br_rental_kind")

    def _get_invoice_type(self):
        # rental transfers go between two internal locations (Rental In and
        # Rental Out), which the generic map reads as a vendor refund: the
        # remessa is a customer document and the retorno the company own entry
        # NF-e (customer refund issued by the company)
        picking = self._l10n_br_rental_pickings()[:1]
        if picking:
            if picking.picking_type_id.l10n_br_rental_kind == "remessa":
                return "out_invoice"
            return "out_refund"
        return super()._get_invoice_type()

    def _get_pickings_with_sale(self, invoice_values):
        # rental transfers are not sale deliveries: the rent is invoiced from
        # the sale order, the transfer NF-e has no sale line
        return super()._get_pickings_with_sale(invoice_values) - (
            self._l10n_br_rental_pickings()
        )

    def _build_invoice_values_from_pickings(self, pickings):
        invoice, values = super()._build_invoice_values_from_pickings(pickings)
        picking = fields.first(pickings)
        if picking.picking_type_id.l10n_br_rental_kind:
            operation = picking.fiscal_operation_id
            values["fiscal_operation_id"] = operation.id
            # the transfer NF-e has no receivable: the lessee payment mode
            # (e.g. boleto) would block its confirmation
            if "payment_mode_id" in values:
                values["payment_mode_id"] = False
            if operation.journal_id:
                values["journal_id"] = operation.journal_id.id
        return invoice, values

    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        values = super()._get_invoice_line_values(moves, invoice_values, invoice)
        move = fields.first(moves)
        if not move.picking_type_id.l10n_br_rental_kind:
            return values
        # The rental moves keep the sale_line_id of the rental service line,
        # so the sale picking invoicing links the NF-e to that line and copies
        # its fiscal data: the rent would count as invoiced and the line would
        # take the rental charge operation. The transfer NF-e follows the stock
        # move only, at the asset value.
        values.pop("sale_line_ids", None)
        values.pop("analytic_distribution", None)
        values["discount"] = 0.0
        fiscal_values = move._prepare_br_fiscal_dict()
        fiscal_values.pop("price_unit", None)
        fiscal_values.pop("quantity", None)
        values.update(fiscal_values)
        price = move.product_id.with_company(move.company_id).standard_price
        values["price_unit"] = price
        values["fiscal_price"] = price
        values["tax_ids"] = [Command.set(move.tax_ids.ids)]
        values["move_line_ids"] = [Command.link(m.id) for m in moves]
        return values
