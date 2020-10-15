# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    repair_fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        string='Operação Fiscal Padrão de Reparos')

    copy_note = fields.Boolean(
        string='Copy Repair note on invoice',
        default=False)
