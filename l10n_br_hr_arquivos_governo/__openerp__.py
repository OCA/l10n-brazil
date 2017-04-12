# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'l10n br hr Arquivos Governo',
    'description': """
        Modulo que gera os arquivos txt da folha de pagamento brasileira""",
    'version': '8.0.0.1',
    'license': 'AGPL-3',
    'author': 'Hendrix Costa',
    'website': 'www.kmee.com.br',
    'depends': [
        'document',
        'l10n_br_hr_payroll',
        'l10n_br_account', # Por causa do Cnae primario
    ],
    'data': [
        'security/hr_payslip.xml',
        'views/hr_payslip.xml',
    ],
}
