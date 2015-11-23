# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Luis Felipe Miléo
#    Copyright 2014 KMEE - www.kmee.com.br
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

{'name': "Bank statement CNAB 240 import",
 'version': '1.0.0',
 'author': 'KMEE',
 'maintainer': 'Luis Felipe Mileo',
 'category': 'Finance',
 'complexity': 'normal',
 'depends': [
     'account_statement_commission',
     'account_statement_transactionid_import'
 ],
 'external_dependencies': {
     'python': ['cnab240'],
 },
 'description': """
    Allows to import CNAB 240 (Centro Nacional de Automação Bancária) statement
     files, using *account_statement_base_import* generic inheritance
      to import statements.

    It requires python cnab240 library to work.
    """,
 'website': 'http://www.kmee.com.br',
 'data': [],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3',
 }
