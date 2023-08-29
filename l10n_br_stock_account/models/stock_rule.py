# Copyright (C) 2020  Magno Costa - Akretion
# Copyright (C) 2016  Renato Lima - Akretion
# Copyright (C) 2016  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _default_fiscal_operation(self):
        return False

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        domain=lambda self: self._fiscal_operation_domain(),
        default=_default_fiscal_operation,
    )

    invoice_state = fields.Selection(
        selection=[("2binvoiced", _("To Be Invoiced")), ("none", _("Not Applicable"))],
        string="Invoice Status",
        default="none",
        copy=False,
        help="Invoiced: an invoice already exists\n"
        "To Be Invoiced: need to be invoiced\n"
        "Not Applicable: no invoice to create",
    )

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if self.fiscal_operation_id:
            move_values["fiscal_operation_id"] = self.fiscal_operation_id.id
            move_values["invoice_state"] = self.invoice_state
        return move_values

    def _get_custom_move_fields(self):
        """The purpose of this method is to be override in order to
        easily add fields from procurement 'values' argument to move data.
        """
        custom_move_fields = super()._get_custom_move_fields()
        custom_move_fields += [
            key
            for key in self.env["l10n_br_fiscal.document.line.mixin"]._fields.keys()
            if key != "product_id"
        ]
        custom_move_fields += ["invoice_state"]
        return custom_move_fields
