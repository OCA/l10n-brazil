# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Queue',
    'summary': """
        Permite o envio assicrono de documentos fiscais""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE INFORMATICA LTDA,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'queue_job',
        'sped',
    ],
    'data': [
        'views/inherited_sped_operacao_base_view.xml',
        'views/inherited_sped_operacao_subsequente_view.xml',
    ],
    'demo': [
    ],
}
