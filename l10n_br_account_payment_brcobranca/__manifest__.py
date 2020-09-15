# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Account Payment Brcobranca',
    'description': """
        Gera Boletos, CNAB de Remessa e Retorno usando
         a Gem brcobranca do Boletosimples""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'www.akretion.com',
    'depends': [
        'l10n_br_account_payment_order',
        'account_move_base_import',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/l10n_br_cnab_retorno_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
        'views/cnab_return_log_view.xml',
        'data/res_config_settings_data.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'test': [
        'tests/invoice_create.yml'
    ]
}
