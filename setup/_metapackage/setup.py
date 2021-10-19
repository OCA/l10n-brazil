import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-brazil",
    description="Meta package for oca-l10n-brazil Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-l10n_br_account_due_list',
        'odoo14-addon-l10n_br_base',
        'odoo14-addon-l10n_br_coa',
        'odoo14-addon-l10n_br_coa_generic',
        'odoo14-addon-l10n_br_coa_simple',
        'odoo14-addon-l10n_br_fiscal',
        'odoo14-addon-l10n_br_nfe_spec',
        'odoo14-addon-spec_driven_model',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
