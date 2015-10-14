# -*- encoding: utf-8 -*-

{
    'name': 'fci',
    'description': """
    Cria arquivos fci para validação
    """,
    'license': 'AGPL-3',
    'author': 'KMEE',
    'version': '8.0',
    'website': 'www.kmee.com.br',
    'depends': [
        # 'account',
        'l10n_br_account_product',
    ],
    'data': [
        'views/l10n_br_fci.xml',
        'workflow/fci_workflow.xml',
        'views/l10n_br_fci_import.xml'
    ],
    'demo': [],
    'category': 'Localization',
    'installable': True,
}