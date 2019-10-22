# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Edoc Base',
    'summary': """
        Base da transmissao de documentos fiscais""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'l10n_br_account_product',
        'document',
    ],
    'data': [
        'views/l10n_br_account_document_event.xml',
        'views/res_company.xml',
        'wizards/edoc_cce_wizard.xml',
        'wizards/edoc_cancel_wizard.xml',
        'views/account_invoice.xml',
    ],
    'demo': [
    ],
}
