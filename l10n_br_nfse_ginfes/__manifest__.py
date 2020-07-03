# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Edoc Nfse Ginfes',
    'summary': """
        NFS-E Ginfes""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-brazil',
    'external_dependencies': {
        'python': [
            'erpbrasil.edoc',
            'erpbrasil.assinatura',
            'erpbrasil.transmissao',
            'erpbrasil.base',
        ],
    },
    'depends': [
        'l10n_br_nfse',
    ],
    'data': [
    ],
    'demo': [
    ],
}
