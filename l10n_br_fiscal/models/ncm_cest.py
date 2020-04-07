# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class NCM(models.Model):
    _inherit = 'l10n_br_fiscal.ncm'

    cest_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.cest',
        relation='fiscal_cest_ncm_rel',
        colunm1='ncm_id',
        colunm2='cest_id',
        readonly=True,
        string='CESTs')
