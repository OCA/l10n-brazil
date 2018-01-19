# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# Bianca Bartolomei <bianca.bartolomei@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
import openerp.tests.common as test_common

class FinanLancamentoPagarManual(test_common.SingleTransactionCase):

    def setUp(self):
        super(FinanLancamentoPagarManual, self).setUp()
        self.finan_lancamento = self.env['finan.lancamento']

        self.finan_lancamento_a_pagar = self.finan_lancamento.create({
            'situacao_divida': 'a_vencer',
            'empresa_id': self.env.ref('l10n_br_base.'
                                       'sped_empresa_regime_normal_sp').id,
            'participante_id':self.env.ref('l10n_br_base.cliente9_mg').id,
            'documento_id':self.env.ref('finan.DOCUMENTO_FINANCEIRO_BOLETO').id,
            'numero':2345,
            'data_documento':fields.Datetime.from_string('2018-01-10 00:00:00'),
            'conta_id':self.env.ref('finan.financial_account_101001').id,
            'data_vencimento':fields.Datetime.from_string('2018-01-10 00:00:00'),
            'forma_pagamento_id':self.env.ref('finan.finan_forma_pagamento_001').id,
            'banco_id':self.env.ref('finan.finan_banco_237').id,
            'vr_documento':100.00,
            'tipo':'a_pagar',
            'carteira_id':self.env.ref('finan.finan_carteira_001').id,
        })

        self.finan_lancamento_a_pagar.confirma_lancamento()

        self.finan_lancamento_pagamento = self.finan_lancamento.create({
            'empresa_id': self.env.ref('l10n_br_base.'
                                       'sped_empresa_regime_normal_sp').id,
            'documento_id':self.env.ref('finan.DOCUMENTO_FINANCEIRO_BOLETO').id,
            'numero':2345,
            'data_credito_debito':fields.Datetime.from_string('2018-01-10 00:00:00'),
            'conta_id':self.env.ref('finan.financial_account_101001').id,
            'data_pagamento':fields.Datetime.from_string('2016-01-10 00:00:00'),
            'forma_pagamento_id':self.env.ref('finan.finan_forma_pagamento_001').id,
            'banco_id':self.env.ref('finan.finan_banco_237').id,
            'vr_documento':70.00,
            'tipo':'recebimento',
            'vr_movimentado':70.00,
            'vr_multa': 0,
            'vr_juros': 0,
            'vr_adiantado': 0,
            'vr_desconto': 0,
            'vr_tarifas': 0,
        })

    def teste1_lancamento_a_pagar_state(self):
        """"
        Teste 1:
        O state de uma conta a pagar deve ser efetivo(open)
        e o provisorio dele, falso
        """
        self.assertEqual(self.finan_lancamento_a_pagar.provisorio, False)
        self.assertEqual(self.finan_lancamento_a_pagar.state, 'open')

    def teste2_lancamento_pagamento_state(self):
        """"
        Teste 2:
        O provisorio deve ser falso
        """
        self.assertEqual(self.finan_lancamento_pagamento.provisorio, False)
        self.assertEqual(self.finan_lancamento_pagamento.state, 'paid')

    def teste3_saldo_divida(self):
        """"
        Teste 3:
        O saldo após a divida ter pagamento deve ser a subtração do valor
        da dívida com o valor do pagamento
        """
        self.finan_lancamento_pagamento.divida_id = self.finan_lancamento_a_pagar.id
        self.assertEqual(self.finan_lancamento_a_pagar.vr_saldo, 30.0)

    def teste4_a_pagar_state(self):
        """"
        Teste 4:
        Após o recebimento, a dívida tem quer ter state quitado(paid)
        """
        self.finan_lancamento_pagamento.divida_id = self.finan_lancamento_a_pagar.id
        self.assertEqual(self.finan_lancamento_a_pagar.state, 'open')