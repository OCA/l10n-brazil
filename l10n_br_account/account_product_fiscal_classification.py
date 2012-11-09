# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2012  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from osv import fields, osv
from tools.translate import _


class account_product_fiscal_classification_template(osv.osv):
    _inherit = 'account.product.fiscal.classification.template'
    
    def _get_taxes(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for fiscal_classification in self.browse(cr, uid, ids,
                                                 context=context):
            fc_id = fiscal_classification.id
            result[fc_id] = {'sale_base_tax_ids': [],
                             'purchase_base_tax_ids': []}
            sale_tax_ids = []
            purchase_tax_ids = []
            for line in fiscal_classification.sale_tax_definition_line:
                sale_tax_ids.append(line.tax_id.id)
            for line in fiscal_classification.purchase_tax_definition_line:
                purchase_tax_ids.append(line.tax_id.id)
            sale_tax_ids.sort()
            purchase_tax_ids.sort()
            result[fc_id]['sale_base_tax_ids'] = sale_tax_ids
            result[fc_id]['purchase_base_tax_ids'] = purchase_tax_ids
        return result
       
    _columns = {
        'type': fields.selection([('view', u'Visão'),
                                  ('normal', 'Normal'),
                                  ('extension','Extensão')], 'Tipo'),
        'parent_id': fields.many2one(
            'account.product.fiscal.classification.template',
            'Parent Fiscal Classification',
            domain="[('type', 'in', ('view', 'normal'))]", select=True),
        'child_ids': fields.one2many(
            'account.product.fiscal.classification.template',
             'parent_id', 'Child Fiscal Classifications'),
        'sale_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.sale.template',
            'fiscal_classification_id', 'Taxes Definitions'),
        'sale_base_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Sale Taxes', multi='all'),
        'purchase_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.purchase.template',
            'fiscal_classification_id', 'Taxes Definitions'),
        'purchase_base_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Purchase Taxes', multi='all')}
    _defaults = {
        'type': 'normal'}

account_product_fiscal_classification_template()


class l10n_br_tax_definition_sale_template(osv.osv):
    _name = 'l10n_br_tax.definition.sale.template'
    _inherit = 'l10n_br_tax.definition.template'
    _columns = {
                'fiscal_classification_id': fields.many2one(
                    'account.product.fiscal.classification.template',
                    'Fiscal Classification', select=True)}

    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        fiscal_classification_id)',
        u'Imposto já existente nesta classificação fiscal!')]

l10n_br_tax_definition_sale_template()


class l10n_br_tax_definition_purchase_template(osv.osv):
    _name = 'l10n_br_tax.definition.purchase.template'
    _inherit = 'l10n_br_tax.definition.template'
    _columns = {
                'fiscal_classification_id': fields.many2one(
                    'account.product.fiscal.classification.template',
                    'Fiscal Classification', select=True)}
    
    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        fiscal_classification_id)',
        u'Imposto já existente nesta classificação fiscal!')]

l10n_br_tax_definition_purchase_template()


class account_product_fiscal_classification(osv.osv):
    _inherit = 'account.product.fiscal.classification'
    
    def _get_taxes(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for fiscal_classification in self.browse(cr, uid, ids,
                                                 context=context):
            fc_id = fiscal_classification.id
            result[fc_id] = {'sale_base_tax_ids': [],
                             'purchase_base_tax_ids': []}
            sale_tax_ids = []
            purchase_tax_ids = []
            for line in fiscal_classification.sale_tax_definition_line:
                sale_tax_ids.append(line.tax_id.id)
            for line in fiscal_classification.purchase_tax_definition_line:
                purchase_tax_ids.append(line.tax_id.id)
            sale_tax_ids.sort()
            purchase_tax_ids.sort()
            result[fc_id]['sale_base_tax_ids'] = sale_tax_ids
            result[fc_id]['purchase_base_tax_ids'] = purchase_tax_ids
        return result
       
    _columns = {
        'type': fields.selection([('view', u'Visão'),
                                  ('normal', 'Normal'),
                                  ('extension','Extensão')], 'Tipo'),
        'parent_id': fields.many2one(
            'account.product.fiscal.classification',
            'Parent Fiscal Classification',
            domain="[('type', 'in', ('view', 'normal'))]", select=True),
        'child_ids': fields.one2many('account.product.fiscal.classification',
                                     'parent_id',
                                     'Child Fiscal Classifications'),
        'sale_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.sale',
            'fiscal_classification_id', 'Taxes Definitions'),
        'sale_base_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Sale Taxes', multi='all'),
        'purchase_tax_definition_line': fields.one2many(
            'l10n_br_tax.definition.purchase',
            'fiscal_classification_id', 'Taxes Definitions'),
        'purchase_base_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Purchase Taxes', multi='all')}
    _defaults = {
        'type': 'normal'}

account_product_fiscal_classification()


class l10n_br_tax_definition_sale(osv.osv):
    _name = 'l10n_br_tax.definition.sale'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
                'fiscal_classification_id': fields.many2one(
                    'account.product.fiscal.classification',
                    'Parent Fiscal Classification', select=True)}
    
    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        fiscal_classification_id)',
        u'Imposto já existente nesta classificação fiscal!')]

l10n_br_tax_definition_sale()


class l10n_br_tax_definition_purchase(osv.osv):
    _name = 'l10n_br_tax.definition.purchase'
    _inherit = 'l10n_br_tax.definition'
    _columns = {
                'fiscal_classification_id': fields.many2one(
                    'account.product.fiscal.classification',
                    'Fiscal Classification', select=True)}
    
    _sql_constraints = [
        ('l10n_br_tax_definition_tax_id_uniq','unique (tax_id,\
        fiscal_classification_id)',
        u'Imposto já existente nesta classificação fiscal!')]

l10n_br_tax_definition_purchase()
