# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Hr Payment Order',
    'summary': """
        Integração da folha de pagamento com as ordens de pagamento""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'account_payment',
        'account_payment_partner',
    ],
    'data': [
        'security/hr_payslip.xml',
        'views/hr_payslip.xml',
        'security/payment_order.xml',
        'views/payment_order.xml',
    ],
    'demo': [
        'demo/hr_payslip.xml',
        'demo/payment_order.xml',
    ],
}
