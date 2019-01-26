# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .product_template import PRODUCT_ORIGIN


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    cfop_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cfop',
        domain="[('internal_type', '=', 'normal')]",
        string='CFOP')

    ind_final = fields.Selection(
        selection=[('0', u'Não'),
                   ('1', u'Sim')],
        string=u'Operação com Consumidor final',
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=False,
        default='0',
        help=u'Indica operação com Consumidor final.')


class AccountFiscalPositionTaxTemplate(models.Model):
    _inherit = 'account.fiscal.position.tax.template'

    fiscal_classification_id = fields.Many2one(
        comodel_name='account.product.fiscal.classification.template',
        string=u'NCM')

    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST')

    tax_ipi_guideline_id = fields.Many2one(
        comodel_name='l10n_br_account_product.ipi_guideline',
        string=u'Enquadramento IPI')

    tax_icms_relief_id = fields.Many2one(
        comodel_name='l10n_br_account_product.icms_relief',
        string=u'Desoneração ICMS')

    origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem')

    cst_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cst',
        string=u'CST',
        required=False)
