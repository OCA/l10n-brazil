# -*- coding: utf-8 -*-
#    Copyright (C) 2012-TODAY KMEE (http://www.kmee.com.br)
#    @author Luis Felipe Miléo (mileo@kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    'name': 'Odoo Brasil Account Payment Boleto',
    'version': '8.0.1.0.0',
    'category': 'Banking addons',
    'license': 'AGPL-3',
    'summary': 'Adds payment mode boleto on move lines',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'http://www.kmee.com.br',
    'depends': [
        'l10n_br_account_payment_mode',
        'account_due_list',
        'base_transaction_id',
    ],
    'data': [
        'data/boleto_data.xml',
        'views/res_company.xml',
        'views/payment_mode.xml',
        'views/account_move_line.xml',
        'views/account_view.xml',
    ],
    'demo': [
        'demo/payment_demo.xml',
        'demo/account_invoice_demo.xml',
    ],
}
