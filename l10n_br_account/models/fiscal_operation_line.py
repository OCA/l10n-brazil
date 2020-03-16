# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class OperationLine(models.Model):
    _inherit = 'l10n_br_fiscal.operation.line'

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        company_dependent=True,
    )

    move_template_id = fields.Many2one(
        comodel_name='l10n_br_account.move.template',
        string='Move Template',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
