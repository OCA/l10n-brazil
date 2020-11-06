# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ...l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK,
)


class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = [_name, 'l10n_br_fiscal.document.line.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return False

    @api.model
    def _fiscal_operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_move_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes",
    )

    quantity = fields.Float(
        related='product_uom_qty',
    )

    uom_id = fields.Many2one(
        related='product_uom',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='picking_id.company_id.tax_framework',
        string='Tax Framework',
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='stock_move_line_comment_rel',
        column1='stock_move_id',
        column2='comment_id',
        string='Comments',
    )

    @api.onchange(
        'product_id',
        'product_uom',
        'product_uom_qty',
        'price_unit')
    def _onchange_product_quantity(self):
        """To call the method in the mixin to update
        the price and fiscal quantity."""
        self._onchange_commercial_quantity()

    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited. """
        result = super()._get_new_picking_values()
        result.update({'fiscal_operation_id': self.fiscal_operation_id.id})
        result.update({'invoice_state': self.invoice_state})
        return result

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields += ['fiscal_operation_id', 'fiscal_operation_line_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super()._prepare_merge_move_sort_method(
            move)
        keys_sorted += [
            move.fiscal_operation_id.id, move.fiscal_operation_line_id.id]
        return keys_sorted

    def _action_confirm(self, merge=True, merge_into=False):
        for record in self:
            record._onchange_commercial_quantity()
            record._onchange_fiscal_taxes()
        return super()._action_confirm(merge, merge_into)

    def _prepare_extra_move_vals(self, qty):
        values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_extra_move_vals(qty))
        values['invoice_state'] = self.invoice_state
        return values

    def _prepare_move_split_vals(self, uom_qty):
        values = self._prepare_br_fiscal_dict()
        values.update(super()._prepare_move_split_vals(uom_qty))
        values['invoice_state'] = self.invoice_state
        return values

    @api.multi
    def _get_price_unit_invoice(self, inv_type, partner, qty=1):
        result = super()._get_price_unit_invoice(inv_type, partner, qty)
        return result

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        result = super()._get_price_unit()
        return result

    @api.onchange('product_id')
    def _onchange_product_id_fiscal(self):
        result = super()._onchange_product_id_fiscal()
        if self.product_id:
            self.price_unit = self._get_price_unit()
        return result
