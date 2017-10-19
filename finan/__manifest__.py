# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Financeiro',
    'summary': """
        Controle Financeiro Brasileiro""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'base',
        'l10n_br_base',
        'mail',
        'report_xlsx',
    ],
    'external_dependencies': {
        'python': ['html2text'],
    },
    'data': [
        'views/finan_view.xml',

        #
        # Cadastros e configurações
        #
        'views/finan_banco_view.xml',
        'views/finan_conta_view.xml',
        'views/finan_documento_view.xml',
        'views/finan_forma_pagamento_view.xml',
        'views/inherited_sped_account_payment_term_view.xml',
        'views/inherited_sped_participante_base_view.xml',

        #
        # Lançamentos
        #
        'views/finan_lancamento_pagamento_one2many_base_view.xml',
        'views/finan_lancamento_pagamento_one2many_recebimento_view.xml',
        'views/finan_lancamento_pagamento_one2many_pagamento_view.xml',

        'views/finan_lancamento_divida_base_view.xml',
        'views/finan_lancamento_divida_a_receber_view.xml',
        'views/finan_lancamento_divida_a_pagar_view.xml',

        #'views/finan_lancamento_pagamento_base_view.xml',

        #
        # Relatórios
        #
        'reports/finan_relatorio_fluxo_caixa_data.xml',
        'wizards/finan_relatorio_fluxo_caixa_wizard.xml',

        'reports/finan_relatorio_divida_data.xml',
        'wizards/finan_relatorio_divida_wizard.xml',

        ##'data/financial_document_type_data.xml',
        ##'data/interest_data.xml',

        #'wizards/financial_cancel.xml',
        ## 'wizards/financial_edit.xml',

        #'wizards/report_xlsx_financial_moves_states_wizard.xml',
        #'wizards/report_xlsx_financial_defaults_wizard.xml',
        #'wizards/report_xlsx_financial_partner_statement_wizard.xml',

        #'views/financial_installment_base_view.xml',
        #'views/financial_installment_2receive_view.xml',
        #'views/financial_installment_2pay_view.xml',

        #'reports/report_xlsx_financial_moves_states_data.xml',

        #'reports/report_xlsx_financial_defaults_data.xml',
        #'reports/report_xlsx_financial_partner_statement_data.xml',

        # Security
        'security/res_groups_data.xml',
        'security/finan_lancamento_ir_rule.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        # 'demo/financial_move.xml',
        # 'demo/financial.account.csv',
        # 'demo/financial_demo.yml'
    ],
    'test': [
        #'test/financial_move_test.yml',
    ]
}
