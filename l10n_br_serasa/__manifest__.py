# Copyright 2015 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Serasa',
    'summary': """
        Integração com os serviços do Serasa""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://odoo-brazil.org',
    'depends': [
	'l10n_br_base',
    ],
    'data': [
        'view/serasa_view.xml',
        'security/serasa_security.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [
    ],
}
