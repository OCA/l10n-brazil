import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_br_account>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_account_due_list>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_base>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_coa>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_coa_generic>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_coa_simple>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_crm>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_currency_rate_update>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_fiscal>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_resource>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_setup_tests>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_stock>=15.0dev,<15.1dev',
        'odoo-addon-l10n_br_zip>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
