# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ...l10n_br_fiscal.constants.fiscal import (
    TAX_FRAMEWORK,
)


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = [
        _name,
        "l10n_br_fiscal.document.mixin",
    ]


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = [
        _name,
        "l10n_br_fiscal.document.line.mixin",
    ]

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_move_line_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes")

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="picking_id.company_id.tax_framework",
        string="Tax Framework")

    # TODO - Is there any reason to keep it ?
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     context = dict(self.env.context)
    #     parent_fiscal_category_id = context.get('parent_fiscal_category_id')
    #     if context.get('company_id'):
    #         company_id = context['company_id']
    #     else:
    #         company_id = self.env.user.company_id.id
    #
    #     result = {'value': {}}
    #     result['value']['invoice_state'] = context.get('parent_invoice_state')
    #
    #     if parent_fiscal_category_id and self.product_id and self.partner_id:
    #
    #         kwargs = {
    #             'partner_id': self.partner_id,
    #             'product_id': self.product_id,
    #             'partner_invoice_id': self.partner_id,
    #             'partner_shipping_id': self.partner_id,
    #             'fiscal_category_id': parent_fiscal_category_id,
    #             'company_id': company_id,
    #             'context': context
    #         }
    #
    #         result.update(self._fiscal_position_map(**kwargs))
    #
    #     result_super = super(StockMove, self).onchange_product_id()
    #     if result_super.get('value'):
    #         result_super.get('value').update(result['value'])
    #     else:
    #         result_super.update(result)
    #     return result_super

    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned to
        another picking. This method is designed to be inherited. """
        result = super(StockMove, self)._get_new_picking_values()
        result.update({'operation_id': self.operation_id.id})
        return result

    @api.onchange("operation_line_id")
    def _onchange_operation_line_id(self):

        # Reset Taxes
        self._remove_all_fiscal_tax_ids()
        if self.operation_line_id:
            mapping_result = self.operation_line_id.map_fiscal_taxes(
                # TODO - We need to inherit this method to identify company and
                #  the TAX FRAMEWORK. Check if there are a better way to do
                company=self.company_id or self.picking_id.company_id,
                partner=self.partner_id,
                product=self.product_id,
                ncm=self.ncm_id,
                nbm=self.nbm_id,
                nbs=self.nbs_id,
                cest=self.cest_id)

            self.cfop_id = mapping_result['cfop']
            taxes = self.env['l10n_br_fiscal.tax']
            for tax in mapping_result['taxes'].values():
                taxes |= tax
            self.fiscal_tax_ids = taxes
            self._update_taxes()

        if not self.operation_line_id:
            self.cfop_id = False
