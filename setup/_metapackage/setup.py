import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_br_account>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_account_due_list>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_account_nfe>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_account_payment_brcobranca>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_account_payment_order>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_base>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_cnab_structure>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_cnpj_search>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_coa>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_coa_generic>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_coa_simple>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_crm>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_currency_rate_update>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_fiscal>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_fiscal_certificate>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_fiscal_closing>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_fiscal_dfe>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_fiscal_edi>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_hr>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_ie_search>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_mis_report>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_nfe>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_nfe_spec>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_nfse>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_nfse_focus>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_purchase>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_resource>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_sale>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_setup_tests>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_stock>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_stock_account>=16.0dev,<16.1dev',
        'odoo-addon-l10n_br_zip>=16.0dev,<16.1dev',
        'odoo-addon-spec_driven_model>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
