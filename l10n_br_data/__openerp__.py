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
    "name" : "Brazilian Localisation Data Extension",
    "description" : "Brazilian Localisation Data Extension",
    "author" : "OpenERP Brasil",
    "version" : "0.1",
    "depends" : [
                 "l10n_br"
                 ],
    'init_xml': [
                #Arquivos com dados Fiscais
                'l10n_br.cfop.csv',
                'l10n_br.fiscal.document.csv',
                'account_product_fiscal_classification_data.xml',
                #Dados dos cadastros de parceiros
                'res.bank.csv',
                'res.country.state.csv',
                'l10n_br.city.csv',
                #Dados da base de CEPs
                #'cep/ac/l10n_br.cep.csv',
                #'cep/al/l10n_br.cep.csv',
                #'cep/am/l10n_br.cep.csv',
                #'cep/ap/l10n_br.cep.csv',
                #'cep/ba/l10n_br.cep.csv',
                #'cep/ce/l10n_br.cep.csv',
                #'cep/df/l10n_br.cep.csv',
                #'cep/es/l10n_br.cep.csv',
                #'cep/go/l10n_br.cep.csv',
                #'cep/ma/l10n_br.cep.csv',
                #'cep/mg/l10n_br.cep.csv',
                #'cep/ms/l10n_br.cep.csv',
                #'cep/mt/l10n_br.cep.csv',
                #'cep/pa/l10n_br.cep.csv',
                #'cep/pb/l10n_br.cep.csv',
                #'cep/pe/l10n_br.cep.csv',
                #'cep/pi/l10n_br.cep.csv',
                #'cep/pr/l10n_br.cep.csv',
                #'cep/rj/l10n_br.cep.csv',
                #'cep/rn/l10n_br.cep.csv',
                #'cep/ro/l10n_br.cep.csv',
                #'cep/rr/l10n_br.cep.csv',
                #'cep/rs/l10n_br.cep.csv',
                #'cep/sc/l10n_br.cep.csv',
                #'cep/se/l10n_br.cep.csv',
                #'cep/sp/l10n_br.cep.csv',
                #'cep/to/l10n_br.cep.csv'
                ],
    "update_xml" : [

                   ],
    "category" : "Localisation",
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
