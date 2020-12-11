# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2010  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

{
    'name' : 'Delivery for Brazilian Localization',
    'description' : 'Extend delivery module for Brazilian Localization',
    'author' : 'OpenERP Brasil',
    'website' : 'http://openerpbrasil.org',
    'version' : '0.6',
    'depends' : [
		'base', 
		'account', 
		'sale', 
		'stock', 
		'delivery',
		],
    'init_xml': [

				],
    'update_xml' :  [
            		'account_invoice_view.xml',
            		'delivery_view.xml',
            		'sale_view.xml',
            		'stock_view.xml',
                    ],
    'category' : 'Localisation',
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
