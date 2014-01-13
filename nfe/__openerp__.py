# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU General Public License for more details.                                 #
#                                                                             #
#You should have received a copy of the GNU General Public License            #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

{
    'name': 'NFE',
    'version': '0.1',
    'category': 'Generic Modules',
    'description': """Implementa a exportação de notas fiscais através de
arquivos XML""",
    'author': 'Akretion, Danimar Ribeiro, Luis Felipe Miléo',
    'license': 'AGPL-3',
    'website': 'http://www.openerpbrasil.org',
    'description': """
      Este módulo é complementar para enviar para a receita a nfe, inutilização e cancelamento de notas.
      Dependencias: pysped, geraldo, pyxmlsec
      Instalando pyxmlsec 
        sudo pip install pyxmlsec
        Dependencias ->
        sudo apt-get install libxmlsec1-dev
        sudo apt-get install libxml2-dev
      Instalando geraldo
        sudo pip install geraldo
    """,
    'depends': [
        'l10n_br_account_product',
        'l10n_br_delivery',
    ],
    'data': [
            'account_invoice_workflow.xml',
             'l10n_br_account_view.xml',
             'account_invoice_view.xml',
            ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
