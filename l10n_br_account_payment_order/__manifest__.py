# Copyright (C) 2016-Today - KMEE (<http://kmee.com.br>).
#  Luis Felipe Miléo - mileo@kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Payment Order',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': "KMEE, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/l10n-brazil',
    'category': 'Banking addons',
    'depends': [
        'l10n_br_base',
        'account_payment_order',
        'account_due_list',
        'account_cancel',
    ],
    'data': [
        # Security]
        'security/cnab_cobranca_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/cnab_data.xml',
        'data/l10n_br_payment_export_type.xml',
        'data/boleto_data.xml',
        'data/ir_cron.xml',
        'data/account_analytic_tag_data.xml',

        # Reports
        'reports/report_print_button_view.xml',

        # Views
        'views/account_due_list.xml',
        'views/account_payment_order.xml',
        'views/account_payment_line.xml',
        'views/account_payment_mode.xml',
        'views/res_company.xml',
        'views/bank_payment_line.xml',
        'views/l10n_br_cnab_retorno_view.xml',
        'views/l10n_br_cnab_evento_views.xml',
        'views/account_invoice.xml',
        'views/account_move_line.xml',
        # 'views/l10n_br_payment_cnab.xml',
        # 'views/l10n_br_cobranca_cnab.xml',
        # 'views/l10n_br_cobranca_cnab_lines.xml',
        # 'views/account_payment_order_menu_views.xml', TODO REMOVE

        # Wizards
        'wizards/account_payment_line_create_view.xml',
    ],
    'demo': [
        'demo/res_partner_bank.xml',
        'demo/account_journal.xml',
        'demo/account_payment_mode.xml',
        'demo/account_payment_order.xml',
        'demo/res_users.xml',
        'demo/account_invoice.xml',
        'demo/res_users.xml',
    ],
    'installable': True,
}
