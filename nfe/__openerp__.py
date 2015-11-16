# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2013  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

{
    'name': 'NFE',
    'version': '8.0.1.0.0',
    'category': 'Generic Modules',
    'author': 'Akretion, Danimar Ribeiro, KMEE',
    'license': 'AGPL-3',
    'website': 'http://www.openerpbrasil.org',
    'description': """
        Implementa a exportação de notas fiscais através de
                        arquivos XML
      Este módulo é complementar para enviar para a receita a nfe,
      inutilização e cancelamento de notas.
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
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/nfe_invoice_cce_view.xml',
        'wizard/nfe_invoice_cancel_view.xml',
        'account_invoice_workflow.xml',
        'views/l10n_br_account_view.xml',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'report/report_print_button_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
}
