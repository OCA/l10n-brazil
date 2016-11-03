# -*- coding: utf-8 -*-
# © 2016 KMEE(http://www.kmee.com.br)
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Account withholdings',
    'description': """
    Brazilian Localization Account withholdings""",
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://www.kmee.com.br',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_account_product_service',
        'l10n_br_sale',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/l10n_br_account_view.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
}
