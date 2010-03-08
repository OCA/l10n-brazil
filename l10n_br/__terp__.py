# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Brazilian Localization',
    'description' : 'Brazilian Localization',
    'author' : 'OpenERP Brasil',
    'version' : '0.1',
    'depends' : [
		'base', 
		'account', 
		'account_chart', 
		'product', 
		'sale', 
		'account_fiscal_position_rule', 
		'account_product_fiscal_classification'
		],
    'init_xml': [
		'data/l10n_br_data.xml',
		'data/account.account.type.csv',
	        'data/account.account.template.csv',
        	'data/account.tax.code.template.csv',     
       		'data/l10n_br_chart_template.xml',
        	'data/account.tax.template.xml',
		],
    'update_xml' : [
        #'security/ir.model.access.csv',       
        'l10n_br_view.xml',
        'country_view.xml',
        'partner_view.xml',
        'l10n_br_wizard.xml',
        'account_invoice_view.xml',
        'account_fiscal_position_rule_view.xml'
    ],
    'category' : 'Localisation/Account Charts',
    'active': False,
    'installable': True
}
