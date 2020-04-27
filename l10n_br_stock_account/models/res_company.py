# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operação Padrão de Estoque',
        domain="[('state', '=', 'approved')]"
    )

    stock_in_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operação Padrão de Entrada',
        domain="[('state', '=', 'approved'), "
               "('operation_type', 'in', ('in', 'all'))]",
    )

    stock_out_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operação Padrão Saída',
        domain="[('state', '=', 'approved'), "
               "('operation_type', 'in', ('out', 'all'))]",
    )
