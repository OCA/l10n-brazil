# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2011  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

{
    'name' : 'Account Payment Extension',
    'description' : 'Brazilian Localization Account Payment Extension',
    'category' : 'Localisation',
    'license': 'AGPL-3',
    'author' : 'Akretion, OpenERP Brasil',
    'website' : 'http://openerpbrasil.org',
    'version' : '0.6',
    'depends' : [
		        'l10n_br_account', 
                'l10n_br_account_payment',
                'account_payment_extension',
		        ],
    'init_xml' : [
		        #'l10n_br_account_payment_extension.csv',
		        ],
    'update_xml' : [
                    'payment_view.xml',
                    'l10n_br_account_payment_extension_data.xml',
		            'account_invoice_view.xml',
                    'security/ir.model.access.csv',
                    'security/l10n_br_account_payment_extension_security.xml',
                    ],
    'demo_xml': [
                'l10n_br_account_payment_extension_demo.xml'
                ],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
