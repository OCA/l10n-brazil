import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-l10n_br_base',
        'odoo12-addon-l10n_br_crm',
        'odoo12-addon-l10n_br_zip',
        'odoo12-addon-l10n_br_zip_correios',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
