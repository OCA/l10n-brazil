# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Relatórios contábeis brasileiros: Balanço Patrimonial e DRE',
    'summary': """
        Templates de relatórios contábeis brasileiros: Balanço Patrimonial e DRE""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-brazil',
    'maintainers': ['mileo'],
    "development_status": "Alpha",
    'depends': [
        'mis_builder',
        'l10n_br_coa',
    ],
    'data': [
        'data/mis_report_styles.xml',

        'data/mis_report_bp.xml',
        'data/mis_report_dre.xml',
    ],
}
