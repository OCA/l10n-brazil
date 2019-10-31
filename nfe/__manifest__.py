# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    'name': 'NFE',
    'version': '10.0.1.0.0',
    'category': 'Generic Modules',
    'author': 'Akretion, Danimar Ribeiro, KMEE, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://odoo-brasil.org',
    'external_dependencies': {
        'python': [
            'pysped'
        ],
    },
    'depends': [
        'edoc_base',
        'barcodes',
    ],
    'data': [
        'data/nfe_attach_email.xml',
        'security/ir.model.access.csv',
        'wizard/nfe_xml_periodic_export.xml',
        'wizard/l10n_br_account_invoice_import.xml',
        'data/nfe_schedule.xml',
        # 'account_invoice_workflow.xml',
        'views/l10n_br_account_view.xml',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/nfe_mde_view.xml',
        'views/account_fiscal_position_view.xml',
        'views/nfe_import_view.xml',
        'report/report_print_button_view.xml',
        'report/report_danfe.xml',
        'wizard/wizard_nfe_import_xml_view.xml',
    ],
    'css': [
        'static/src/css/nfe_import.css'
    ],
    'demo': [],
    'test': [],
    'installable': True,
}
