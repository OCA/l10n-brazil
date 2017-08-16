# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Brazilian Localization Participantes Geolocation',
    'summary': """
        Vendas Brasileira""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'base_geolocalize',
        'l10n_br_base',
    ],
    'data': [
        'views/sped_participante.xml',
    ],
    'installable': True,
}

