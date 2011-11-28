# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
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
    "name" : "Brazilian Localisation Data Extension for Base with brazilian zip codes",
    "description" : "Brazilian Localisation Data Extension for Base with brazilian zip codes",
    'license': 'AGPL-3',
    "author" : "Akretion, OpenERP Brasil",
    "version" : "0.1",
    "depends" : [
                 "l10n_br_base"
                 ],
    'init_xml': [
                'zip/ac/l10n_br_base.zip.csv',
                'zip/al/l10n_br_base.zip.csv',
                'zip/am/l10n_br_base.zip.csv',
                'zip/ap/l10n_br_base.zip.csv',
                'zip/ba/l10n_br_base.zip.csv',
                'zip/ce/l10n_br_base.zip.csv',
                'zip/df/l10n_br_base.zip.csv',
                'zip/es/l10n_br_base.zip.csv',
                'zip/go/l10n_br_base.zip.csv',
                'zip/ma/l10n_br_base.zip.csv',
                'zip/mg/l10n_br_base.zip.csv',
                'zip/ms/l10n_br_base.zip.csv',
                'zip/mt/l10n_br_base.zip.csv',
                'zip/pa/l10n_br_base.zip.csv',
                'zip/pb/l10n_br_base.zip.csv',
                'zip/pe/l10n_br_base.zip.csv',
                'zip/pi/l10n_br_base.zip.csv',
                'zip/pr/l10n_br_base.zip.csv',
                'zip/rj/l10n_br_base.zip.csv',
                'zip/rn/l10n_br_base.zip.csv',
                'zip/ro/l10n_br_base.zip.csv',
                'zip/rr/l10n_br_base.zip.csv',
                'zip/rs/l10n_br_base.zip.csv',
                'zip/sc/l10n_br_base.zip.csv',
                'zip/se/l10n_br_base.zip.csv',
                'zip/sp/l10n_br_base.zip.csv',
                'zip/to/l10n_br_base.zip.csv'
                ],
    "update_xml" : [

                   ],
    "category" : "Localisation",
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
