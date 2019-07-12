# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class TaxIpiGuideline(models.Model):
    _name = 'l10n_br_fiscal.tax.ipi.guideline'
    _description = 'IPI Guidelines'
    _inherit = 'l10n_br_fiscal.data.abstract'

    code = fields.Char(
        size=3)

    cst_group = fields.Selection(
        selection=[('imunidade', u'Imunidade'),
                   ('suspensao', u'Suspensão'),
                   ('isencao', u'Isenção'),
                   ('reducao', u'Redução'),
                   ('outros', u'Outros')],
        string='Group',
        required=True)

    cst_in_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        domain=[('domain', '=', 'ipi'),
                ('type', '=', 'in')],
        string=u'CST In')

    cst_out_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        domain=[('domain', '=', 'ipi'),
                ('type', '=', 'out')],
        string=u'CST Out')
