# Copyright 2020 - TODAY, Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Localization Repair',
    'summary': """
        Brazilian Localization Repair""",
    'version': '12.0.1.0.0',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author':
        'Escodoo, '
        'Odoo Community Association (OCA)',
    'maintainers': ['marcelsavegnago'],
    'website': 'https://github.com/OCA/l10n-brazil',
    'depends': [
        'repair',
        'l10n_br_account',
    ],
    'data': [
        'demo/res_company.xml',
        'security/l10n_br_repair_security.xml',
        'views/res_company.xml',
        'views/repair_order.xml',
        'views/repair_fee.xml',
        'views/repair_line.xml',
    ],
    'demo': [
        'demo/res_company.xml',
    ],
    'installable': True,
    'auto_install': True,
    'development_status': 'Production/Beta',
    'conflicts': ['repair_discount'],
    'external_dependencies': {'python': ['erpbrasil.base']}

}
