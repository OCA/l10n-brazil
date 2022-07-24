import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-l10n_br_account',
        'odoo14-addon-l10n_br_account_due_list',
        'odoo14-addon-l10n_br_account_nfe',
        'odoo14-addon-l10n_br_account_payment_brcobranca',
        'odoo14-addon-l10n_br_account_payment_order',
        'odoo14-addon-l10n_br_base',
        'odoo14-addon-l10n_br_coa',
        'odoo14-addon-l10n_br_coa_generic',
        'odoo14-addon-l10n_br_coa_simple',
        'odoo14-addon-l10n_br_contract',
        'odoo14-addon-l10n_br_crm',
        'odoo14-addon-l10n_br_currency_rate_update',
        'odoo14-addon-l10n_br_fiscal',
        'odoo14-addon-l10n_br_hr',
        'odoo14-addon-l10n_br_mis_report',
        'odoo14-addon-l10n_br_nfe',
        'odoo14-addon-l10n_br_nfe_spec',
        'odoo14-addon-l10n_br_nfse',
        'odoo14-addon-l10n_br_portal',
        'odoo14-addon-l10n_br_purchase',
        'odoo14-addon-l10n_br_resource',
        'odoo14-addon-l10n_br_sale',
        'odoo14-addon-l10n_br_stock',
        'odoo14-addon-l10n_br_website_sale',
        'odoo14-addon-l10n_br_zip',
        'odoo14-addon-payment_pagseguro',
        'odoo14-addon-spec_driven_model',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
