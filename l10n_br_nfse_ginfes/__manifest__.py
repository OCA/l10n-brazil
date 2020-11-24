# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'NFS-e (Ginfes)',
    'summary': """
        NFS-e (Ginfes)""",
    'version': '12.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'KMEE, Odoo Community Association (OCA)',
    'maintainers': ['gabrielcardoso21', 'mileo', 'luismalta'],
    'website': 'https://github.com/OCA/l10n-brazil',
    "development_status": "Alpha",
    'external_dependencies': {
        'python': [
            'erpbrasil.edoc',
            'erpbrasil.assinatura',
            'erpbrasil.transmissao',
            'erpbrasil.base',
            'nfselib.ginfes',
        ],
    },
    'depends': [
        'l10n_br_nfse',
    ],
}
