# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Brazilian Localization Stock Account Report',
    'version': '12.0.1.0.0',
    'author': 'Akretion,'
              'Odoo Community Association (OCA)',
    'category': 'Reports/QWeb',
    'license': 'AGPL-3',
    'depends': [
        'l10n_br_stock_account',
    ],
    'website': 'https://github.com/OCA/l10n-brazil',
    'development_status': 'Mature',
    'maintainers': [
        'mbcosta',
    ],
    'data': [
        'report/l10n_br_stock_account_p7_report.xml',
        'report/l10n_br_stock_account_p7_report_view.xml',
        'wizards/l10n_br_stock_account_p7_wizard_report_view.xml'
    ],
    'installable': True,
}
