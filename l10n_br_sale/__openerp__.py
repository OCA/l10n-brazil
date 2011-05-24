# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
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
    'name' : 'Brazilian Localization Sale',
    'description' : 'Brazilian Localization for Sale',
    'category' : 'Localisation',
    'author' : 'Akretion, OpenERP Brasil',
    'website' : 'http://openerpbrasil.org',
    'version' : '0.6',
    'depends' : [
		'l10n_br_account',
		'account_fiscal_position_rule_sale',
		'l10n_br_stock',
		],
    'init_xml': [],
    'update_xml' : [
		'sale_view.xml',
    ],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
