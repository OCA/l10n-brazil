# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Financial',
    'summary': """
        Financeiro brasileiro (Tesouraria e Integracao Bancaria)""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.odoobrasil.org.br',
    'depends': [
        'financial',
        'sped_sale',
        'l10n_br_base',
    ],
    'data': [
        'views/financial_move.xml',
        'views/account_payment_term.xml',
        'views/sped_participante.xml',
        'views/sale_order.xml',
        'views/financial_installment.xml',
    ],
    'demo': [
        'demo/financeiro_tipo_documento.xml',
    ],
    'installable': True,
}
