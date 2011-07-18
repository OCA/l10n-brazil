# -*- encoding: utf-8 -*-
#################################################################################
#
#    Copyright (C) 2009  Renato Lima - Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

{
    'name': 'Brazilian Localization',
    'description': 'Brazilian Localization',
    'category': 'Localisation/Account Charts',
    'license': 'Affero GPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '0.6',
    'depends': ['account','account_chart'],
    'init_xml': [        
        'data/account.account.type.csv',
        'data/account.tax.code.template.csv',
        'data/account.account.template.csv',
        'data/l10n_br_account_chart_template.xml',
        'data/account_tax_template.xml',
        'data/l10n_br_data.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_security.xml',
                ],
    'update_xml': [
        'account_view.xml',
        'l10n_br_view.xml',
    ],
    'installable': True,
    'certificate' : '001280994939126801405',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
