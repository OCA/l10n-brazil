# Copyright 2017 KMEE INFORMATICA LTDA
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

{
    'name': 'CF-E - MFE e SAT',
    'version': '12.0.1.0.0',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'category': 'Fiscal',
    'depends': [
        'l10n_br_fiscal',
        'report_py3o',
        'base',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',  # FIXME

        'report/cfe_report.xml',

        'wizard/wizard_document_payment_view.xml',

        'views/l10n_br_cfe_menu_view.xml',
        'views/l10n_br_pdv_config_view.xml',
        'views/l10n_br_pdv_impressora_config_view.xml',

        'views/res_user_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',

        'views/document_emissao_cfe_view.xml',
        'views/document_payment_view.xml',

        # 'views/fiscal_operation_cfe_.xml.xml',
        # 'views/web_asset_backend_template.xml',
    ],
    'demo': [
        'demo/pos_config_demo.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'external_dependencies': {
        'python': [
            'erpbrasil.base',
            'satcfe',
        ],
    }
}
