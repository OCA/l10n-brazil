# -*- coding: utf-8 -*-
# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Account Payment Boleto Brcobranca',
    'description': """
        Imprime boletos usando a Gem brcobranca do Boletosimples""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'www.akretion.com',
    'depends': [
        'l10n_br_account_payment_boleto',
    ],
    'data': [
        'reports/report_print_button_view.xml',
    ],
    'demo': [
    ],
}
