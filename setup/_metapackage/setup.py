import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo8-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo8-addon-l10n_br_account',
        'odoo8-addon-l10n_br_account_banking_payment',
        'odoo8-addon-l10n_br_account_product',
        'odoo8-addon-l10n_br_account_product_service',
        'odoo8-addon-l10n_br_account_service',
        'odoo8-addon-l10n_br_base',
        'odoo8-addon-l10n_br_crm',
        'odoo8-addon-l10n_br_crm_zip',
        'odoo8-addon-l10n_br_data_account',
        'odoo8-addon-l10n_br_data_account_product',
        'odoo8-addon-l10n_br_data_account_service',
        'odoo8-addon-l10n_br_data_base',
        'odoo8-addon-l10n_br_delivery',
        'odoo8-addon-l10n_br_hr',
        'odoo8-addon-l10n_br_hr_contract',
        'odoo8-addon-l10n_br_purchase',
        'odoo8-addon-l10n_br_sale',
        'odoo8-addon-l10n_br_sale_product',
        'odoo8-addon-l10n_br_sale_service',
        'odoo8-addon-l10n_br_sale_stock',
        'odoo8-addon-l10n_br_stock',
        'odoo8-addon-l10n_br_stock_account',
        'odoo8-addon-l10n_br_stock_account_report',
        'odoo8-addon-l10n_br_zip',
        'odoo8-addon-l10n_br_zip_correios',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
