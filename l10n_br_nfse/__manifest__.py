# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Edoc Nfse',
    'summary': """
        NFS-E""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'website': 'https://kmee.com.br',
    'external_dependencies': {
        'python': [
            'erpbrasil.edoc',
            'erpbrasil.assinatura',
            'erpbrasil.transmissao',
            'erpbrasil.base',
        ],
    },
    'depends': [
        'l10n_br_fiscal',
    ],
    'data': [
        'security/account_invoice.xml',
        'views/account_invoice.xml',
    ],
    'demo': [
        'demo/account_invoice.xml',
    ],
}
