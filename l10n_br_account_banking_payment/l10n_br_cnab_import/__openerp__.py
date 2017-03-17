# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Fernando Marcato Rodrigues
#    Copyright 2015 KMEE - www.kmee.com.br
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
    'name': 'Import CNAB Bank Statement',
    'version': '8.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['cnab240'],
    },
    'depends': [
        'account_bank_statement_import',
        'l10n_br_account',
    ],
    'data': [
        'view/cnab_import_view.xml',
    ],
    'active': False,
    "installable": True,
    "auto_install": False,
    'description': """
    Allows to import CNAB (Centro Nacional de Automação Bancária) statement
     files.

    It requires python PyCNAB library to work.
    """,
}
