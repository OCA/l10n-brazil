# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class NCM(models.Model):
    _inherit = 'l10n_br_fiscal.ncm'

    nbm_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.nbm',
        relation='fiscal_nbm_ncm_rel',
        colunm1='ncm_id',
        colunm2='nbm_id',
        readonly=True,
        string='NBMs')
