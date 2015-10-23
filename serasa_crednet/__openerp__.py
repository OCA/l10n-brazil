# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian 5 acts module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Mileo <mileo@kmee.com.br>
#    @author Matheus Lima Felix <matheus.felix@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Serasa Crednet',
    'version': '8.0.1.0.0',
    'author': 'KMEE',
    'website' : 'http://www.kmee.com.br',
    'category' : 'Accounting & Finace',
    'sequence' : 32,
    'depends': ['l10n_br_base'],
    'data' : ['view/serasa_view.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}