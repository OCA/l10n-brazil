# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operação Fiscal Padrão de Estoque')
    stock_in_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string=u'Categoria Fiscal Padrão de Entrada',
        # TODO - domain
        # domain="[('journal_type', 'in', ('sale_refund', 'purchase')), "
        # "('fiscal_type', '=', 'product'), ('type', '=', 'input')]"
    )
    stock_out_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string=u'Categoria Fiscal Padrão Saída',
        # TODO - domain
        # domain="[('journal_type', 'in', ('purchase_refund', 'sale')), "
        # "('fiscal_type', '=', 'product'), ('type', '=', 'output')]"
    )
