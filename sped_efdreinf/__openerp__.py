# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Wagner Pereira
#    Copyright 2018 ABGF - www.abgf.gov.br
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
    'name': 'Sped EFD/Reinf',
    'version': '8.0.0.0.1',
    'category': 'Base',
    'license': 'AGPL-3',
    'author': 'ABGF',
    'website': 'http://www.abgf.gov.br',
    'depends': [
        'sped_transmissao',
        'l10n_br_account_product',
    ],
    'data': [

        # Menus
        'views/sped_efdreinf_menu.xml',

        # Views
        'views/sped_efdreinf_view.xml',
        'views/inherited_product_template.xml',
        'views/inherited_res_company.xml',

        # View/intermediários
        'views/intermediarios/r1000_informacoes_contribuinte_view.xml',
        # Segurança
        'security/ir.model.access.csv',

    ],
    "installable": True,
    "auto_install": False,
}
