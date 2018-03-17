# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA, Grupo Zenir
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Mdfe',
    'summary': """
        Emissão de Manifesto Eletrônico de Documentos Fiscais (MDF-e)""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA, Grupo Zenir,Odoo Community Association (OCA)',
    'depends': [
        'sped_nfe',
    ],
    'data': [
        'security/sped_operacao.xml',
        'views/sped_operacao.xml',
    ],
    'demo': [
        'demo/sped_operacao.xml',
    ],
}
