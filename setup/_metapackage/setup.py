import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-l10n_br_account_payment_order',
        'odoo12-addon-l10n_br_base',
        'odoo12-addon-l10n_br_crm',
        'odoo12-addon-l10n_br_currency_rate_update',
        'odoo12-addon-l10n_br_hr',
        'odoo12-addon-l10n_br_hr_contract',
        'odoo12-addon-l10n_br_portal',
        'odoo12-addon-l10n_br_resource',
        'odoo12-addon-l10n_br_simple',
        'odoo12-addon-l10n_br_stock',
        'odoo12-addon-l10n_br_zip',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
