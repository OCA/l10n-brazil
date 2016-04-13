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
    'name': 'Import CNAB 400 Bank Statement',
    'version': '0.1',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'author': 'KMEE',
    'website': 'http://www.kmee.com.br',
    'external_dependencies': {
        'python': ['cnab240'],
    },
    'depends': [
        'l10n_br_account',
        'account_bank_statement_import',
    ],
    'data': [
        'view/l10n_br_cnab_move_view.xml',
        'view/account_move_line_view.xml',
        'data/l10n_br_res_partner_bank_type.xml',
    ],
    'active': False,
    "installable": True,
    "auto_install": False,
    'description': """
    Allows to import CNAB 400 (Centro Nacional de Automação Bancária)
    statement files.

    It requires python PyCNAB library to work.
    """,
}
