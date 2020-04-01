# Copyright (C) 2012  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class TaxEstimate(models.Model):
    _name = 'l10n_br_fiscal.tax.estimate'
    _description = 'Fiscal Tax Estimate'
    _order = 'create_date desc'

    ncm_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.ncm',
        string='NCM')

    nbs_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.nbs',
        string='NBS')

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        required=True)

    federal_taxes_national = fields.Float(
        string='Impostos Federais Nacional',
        default=0.00,
        digits=dp.get_precision('Fiscal Tax Percent'))

    federal_taxes_import = fields.Float(
        string='Impostos Federais Importado',
        default=0.00,
        digits=dp.get_precision('Fiscal Tax Percent'))

    state_taxes = fields.Float(
        string='Impostos Estaduais Nacional',
        default=0.00,
        digits=dp.get_precision('Fiscal Tax Percent'))

    municipal_taxes = fields.Float(
        string='Impostos Municipais Nacional',
        default=0.00,
        digits=dp.get_precision('Fiscal Tax Percent'))

    create_date = fields.Datetime(
        string='Create Date',
        readonly=True)

    key = fields.Char(
        string='Key',
        size=32)

    origin = fields.Char(
        string='Source',
        size=32)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n_br_fiscal.tax.estimate'))
