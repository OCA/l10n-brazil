import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-l10n_br_account',
        'odoo10-addon-l10n_br_account_payment_order',
        'odoo10-addon-l10n_br_account_product',
        'odoo10-addon-l10n_br_base',
        'odoo10-addon-l10n_br_crm',
        'odoo10-addon-l10n_br_crm_zip',
        'odoo10-addon-l10n_br_generic',
        'odoo10-addon-l10n_br_hr',
        'odoo10-addon-l10n_br_resource',
        'odoo10-addon-l10n_br_stock',
        'odoo10-addon-l10n_br_zip',
        'odoo10-addon-l10n_br_zip_correios',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
