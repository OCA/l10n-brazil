# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Fiscal',
    'summary': 'Brazilian fiscal core module.',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, '
              'Odoo Community Association (OCA)',
    'website': 'http://github.com/OCA/l10n-brazil',
    'version': '12.0.1.0.0',
    'depends': [
        'uom',
        'decimal_precision',
        'product',
        'l10n_br_base'
    ],
    'data': [
        # security
        'security/fiscal_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/fiscal_data.xml',
        'data/uom_data.xml',
        'data/fiscal.cnae.csv',
        'data/fiscal.document.type.csv',
        'data/fiscal.product.genre.csv',
        'data/fiscal.cfop.csv',
        'data/fiscal.cst.csv',
        'data/fiscal.tax.csv',
        'data/fiscal.ncm.csv',
        'data/fiscal.nbs.csv',
        'data/fiscal.cest.csv',

        # Views
        'views/cnae_view.xml',
        'views/cfop_view.xml',
        'views/cst_view.xml',
        'views/fiscal_action.xml',
        'views/fiscal_menu.xml',

        # 'data/l10n_br_account_product_sequence.xml',
        # 'data/l10n_br_account_data.xml',
        # 'data/l10n_br_account_product_data.xml',
        # 'data/l10n_br_tax.icms_partition.csv',
        # 'data/ir_cron.xml',
        # 'views/l10n_br_account_fiscal_category_view.xml',
        # 'views/l10n_br_account_partner_fiscal_type_view.xml',
        # 'views/l10n_br_account_product_ipi_guideline_view.xml',
        # 'views/l10n_br_account_product_icms_relief_view.xml',
        # 'views/l10n_br_account_product_import_declaration_view.xml',
        # 'views/l10n_br_tax_icms_partition_view.xml',
        # 'views/account_tax_template_view.xml',
        # 'views/account_payment_term_view.xml',
        # 'views/account_tax_view.xml',
        # 'views/account_payment_term_view.xml',
        # 'views/account_invoice_view.xml',
        # 'wizards/l10n_br_account_invoice_costs_ratio_view.xml',
        # 'views/nfe/account_invoice_nfe_view.xml',
        # 'views/account_fiscal_position_view.xml',
        # 'views/res_company_view.xml',
        # 'views/account_product_fiscal_classification_template_view.xml',
        # 'views/account_product_fiscal_classification_view.xml',
        # 'views/product_template_view.xml',
        # 'views/res_country_view.xml',
        # 'views/account_payment_mode.xml',
        # 'wizards/l10n_br_account_nfe_export_invoice_view.xml',
        # 'wizards/l10n_br_account_nfe_export_view.xml',
        # 'wizards/l10n_br_account_document_status_sefaz_view.xml',
        # 'wizards/account_invoice_refund_view.xml',
        # 'report/account_invoice_report_view.xml',
    ],
    'demo': [
        # 'demo/account_tax_demo.xml',
        # 'demo/base_demo.xml',
        # 'demo/product_demo.xml',
        # 'demo/l10n_br_account_product_demo.xml',
        # 'demo/account_fiscal_position_rule_demo.xml',
        # 'demo/product_taxes.yml',
        # 'demo/account_invoice_demo.yml',
        # 'demo/account_invoice_demo.xml',
        # 'demo/account_nfe_demo.yml',
        # 'demo/account_nfe_demo.xml',
        # 'demo/account_nfe_supplier_demo.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
