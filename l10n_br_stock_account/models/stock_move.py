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
    def _default_operation(self):
        return False

    @api.model
    def _operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [('state', '=', 'approved')]
        return domain

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_operation,
        domain=lambda self: self._operation_domain(),
    )

    quantity = fields.Float(
        related='product_uom_qty',
    )

    uom_id = fields.Many2one(
        related='product_uom',
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_move_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes",
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='picking_id.company_id.tax_framework',
        string='Tax Framework',
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
        result = super(StockMove, self)._get_new_picking_values()
        result.update({'operation_id': self.operation_id.id})
        return result

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(
            StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields += ['operation_id', 'operation_line_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted += [move.operation_id.id, move.operation_line_id.id]
        return keys_sorted

    def _prepare_extra_move_vals(self, qty):
        vals = super(StockMove, self)._prepare_extra_move_vals(qty)
        vals['operation_id'] = self.operation_id.id
        vals['operation_line_id'] = self.operation_line_id.id
        return vals

    def _prepare_move_split_vals(self, uom_qty):
        vals = super(StockMove, self)._prepare_move_split_vals(uom_qty)
        vals['operation_id'] = self.operation_id.id
        vals['operation_line_id'] = self.operation_line_id.id
        return vals
