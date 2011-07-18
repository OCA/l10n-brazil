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
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

{
    'name' : 'CRM',
    'description' : 'Brazilian Localization for CRM module',
    'category' : 'Localisation',
    'license': 'AGPL-3',
    'author' : 'Akretion, OpenERP Brasil',
    'website' : 'http://openerpbrasil.org',
    'version' : '0.6',
    'depends' : [
		'l10n_br_base', 
		'crm',
		],
    'init_xml': [

		],
    'update_xml' : [
                    'crm_lead_view.xml',
                    'crm_opportunity_view.xml',
                    ],
    'demo_xml': [],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
