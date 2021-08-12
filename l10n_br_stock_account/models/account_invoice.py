# Copyright (C) 2021 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _get_last_step_stock_moves(self):
        """
        This is used to reconcile the COGS/CMV/Remessa invoice lines
        with their matching permanent inventory interim moves. But in Brazil
        we may have incoming or outgoing remessas without a sale or a purchase order.
        """
        rslt = super(AccountInvoice, self)._get_last_step_stock_moves()

        # outgoing remessas:
        for invoice in self.filtered(lambda x: x.type == "out_invoice"):
            rslt += invoice.mapped("invoice_line_ids.move_line_ids").filtered(
                lambda x: (
                    x not in rslt
                    and x.state == "done"
                    and x.location_dest_id.usage == "customer"
                )
            )
        for invoice in self.filtered(lambda x: x.type == "out_refund"):
            rslt += invoice.mapped("invoice_line_ids.move_line_ids").filtered(
                lambda x: (
                    x not in rslt
                    and x.state == "done"
                    and x.location_id.usage == "customer"
                )
            )

        # incoming remessas:
        for invoice in self.filtered(lambda x: x.type == "in_invoice"):
            rslt += invoice.mapped("invoice_line_ids.move_line_ids").filtered(
                lambda x: (
                    x not in rslt
                    and x.state == "done"
                    and x.location_dest_id.usage == "supplier"
                )
            )
        for invoice in self.filtered(lambda x: x.type == "in_refund"):
            rslt += invoice.mapped("invoice_line_ids.move_line_ids").filtered(
                lambda x: (
                    x not in rslt
                    and x.state == "done"
                    and x.location_id.usage == "supplier"
                )
            )

        return rslt

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        """
        Similar to the stock_account _anglo_saxon_sale_move_lines method
        but overriden to take the fiscal position of the operation line into account
        !!WARNING WE COULD NOT CALL SUPER!!
        """
        inv = i_line.invoice_id
        company_currency = inv.company_id.currency_id
        price_unit = i_line._get_anglo_saxon_price_unit()
        if inv.currency_id != company_currency:
            currency = inv.currency_id
            amount_currency = i_line._get_price(company_currency, price_unit)
        else:
            currency = False
            amount_currency = False

        product = i_line.product_id.with_context(force_company=self.company_id.id)
        if (
            i_line.fiscal_operation_line_id
            and i_line.fiscal_operation_line_id.fiscal_position_id
        ):
            fiscal_position = i_line.fiscal_operation_line_id.fiscal_position_id
        else:
            fiscal_position = inv.fiscal_position_id
        return self.env["product.product"]._anglo_saxon_sale_move_lines(
            i_line.name,
            product,
            i_line.uom_id,
            i_line.quantity,
            price_unit,
            currency=currency,
            amount_currency=amount_currency,
            fiscal_position=fiscal_position,
            account_analytic=i_line.account_analytic_id,
            analytic_tags=i_line.analytic_tag_ids,
        )
