# -*- encoding: utf-8 -*-
##############################################################################
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "SPED FISCAL",
    "version": "8.0.0.0.1",
    "depends": [
        "l10n_br_account_product",
    ],
    "author": "KMEE - www.kmee.com.br,",
    "website": "http://www.kmee.com.br",
    "category": "Accounting",
    "description": """ """,
    'data': [
        # "security/ir.model.access.csv",
        # "wizard/wiz_create_invoice_view.xml",
        # "views/account_treasury_forecast_view.xml",
        "views/l10n_br_sped_fiscal_view.xml",
        # "views/account_treasury_forecast_template_view.xml",
    ],
    'demo': [],
    'installable': True,
}
