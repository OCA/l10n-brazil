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
                #'zip/ac/ac.sql',
                #'zip/al/al.sql',
                #'zip/am/am.sql',
                #'zip/ap/ap.sql',
                #'zip/ba/ba.sql',
                #'zip/ce/ce.sql',
                #'zip/df/df.sql',
                #'zip/es/es.sql',
                #'zip/go/go.sql',
                #'zip/ma/ma.sql',
                #'zip/mg/mg.sql',
                #'zip/ms/ms.sql',
                #'zip/mt/mt.sql',
                #'zip/pa/pa.sql',
                #'zip/pb/pb.sql',
                #'zip/pe/pe.sql',
                #'zip/pi/pi.sql',
                #'zip/pr/pr.sql',
                #'zip/rj/rj.sql',
                #'zip/rn/rn.sql',
                #'zip/ro/ro.sql',
                #'zip/rr/rr.sql',
                #'zip/rs/rs.sql',
                #'zip/sc/sc.sql',
                #'zip/se/se.sql',
                #'zip/sp/sp.sql',
                #'zip/to/to.sql'
                'zip.sql'
                ],
    "update_xml" : [

                   ],
    "category" : "Localisation",
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
