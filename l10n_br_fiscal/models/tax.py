# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..constants.fiscal import TAX_DOMAIN

from ..constants.icms import (
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT)


class Tax(models.Model):
    _name = 'l10n_br_fiscal.tax'
    _order = 'tax_domain, name'
    _description = 'Tax'

    name = fields.Char(
        string='Name',
        size=256,
        required=True)

    percent_amount = fields.Float(
        string='Percent',
        default='0.00',
        required=True)

    percent_reduction = fields.Float(
        string='Percent Reduction',
        default='0.00',
        required=True)

    tax_group_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.tax.group',
        string='Fiscal Tax Group')

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related='tax_group_id.tax_domain',
        string='Tax Domain',
        required=True)

    cst_in_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST In',
        domain="[('cst_type', 'in', ('in', 'all')), "
               "('tax_domain', '=', tax_domain)]")

    cst_out_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cst',
        string='CST Out',
        domain="[('cst_type', 'in', ('out', 'all')), "
               "('tax_domain', '=', tax_domain)]")

    icms_base_type = fields.Selection(
        selection=ICMS_BASE_TYPE,
        string=u'Tipo Base ICMS',
        required=True,
        default=ICMS_BASE_TYPE_DEFAULT)

    icms_st_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string=u'Tipo Base ICMS ST',
        required=True,
        default=ICMS_ST_BASE_TYPE_DEFAULT)

    _sql_constraints = [
        ('fiscal_tax_code_uniq', 'unique (name)',
         'Tax already exists with this name !')]

    def _compute_ipi(self):
        pass

    def _compute_icms(self):
        pass

    def _compute_icmsst(self):
        pass

    def _compute_icms_difal(self):
        pass

    def _compute_ii(self):
        pass

    def _compute_pis(self):
        pass

    def _compute_cofins(self):
        pass

    @api.multi
    def compute_taxes(self):
        pass
