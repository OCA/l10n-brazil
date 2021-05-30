# Copyright 2020 - TODAY, Escodoo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Plano de Contas Completo',
    'summary': """
        Plano de Contas Completo para empresas Simples,
        Presumido, Real, SA, Consolidação""",
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Escodoo, Odoo Community Association (OCA)',
    'maintainers': ['marcelsavegnago'],
    'website': 'https://github.com/OCA/l10n-brazil',
    'images': ['static/description/banner.png'],
    'depends': ['l10n_br_coa'],
    'data': [
        'data/l10n_br_coa_complete_template.xml',
        'data/account_group.xml',
        'data/account.account.template.csv',
        'data/account_tax_group.xml',
        'data/account_fiscal_position_template.xml',
        'data/l10n_br_coa_complete_template_post.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
