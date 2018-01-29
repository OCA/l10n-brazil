# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# Isabella Maia Bitencourt <isabella.maia@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields
import openerp.tests.common as test_common

class FinanLancamentoPagarManual(test_common.SingleTransactionCase):

    def setUp(self):
        super(FinanLancamentoPagarManual, self).setUp()
        self.finan_lancamento = self.env['finan.lancamento']
        self.finan_lancamento_a_pagar = self.finan_lancamento.create({
            'situacao_divida': 'a vencer',
            'empresa_id': self.env.ref("l10n_br_base.sped_empresa"
                                       "_regime_normal_sp").id,
            'participante_id': self.env.ref("l10n_br_base.cliente9_mg").id,
            'documento_id': self.env.ref("finan.DOCUMENTO_FINANCEIRO_"
                                         "BOLETO").id,
            'numero': 0003,
            'data_documento': fields.Datetime.from_string('2018-02-21 '
                                                          '23:59:59'),
            'conta_id': self.env.ref("finan.financial_account_101001"),
            'data_vencimento': fields.Datetime.from_string('2018-12-21 '
                                                          '23:59:59'),
            'forma_pagamento_id': self.env.ref("finan.finan_forma_"
                                               "pagamento_001"),
            'banco_id': self.env.ref("finan.finan_banco_237"),
            'vr_documento': 15.50,
            'tipo': 'a_pagar',
            'carteira_id': self.env.ref('finan.finan_carteira_001').id,
        })

        self.finan_lancamento_a_pagar.confirma_lancamento()
        self.finan_lancamento_pagamento = self.finan_lancamento.create({
            'empresa_id': self.env.ref('l10n_br_base.'
                                       'sped_empresa_regime_normal_sp').id,
            'documento_id':self.env.ref('finan.DOCUMENTO_FINANCEIRO_BOLETO').id,
            'numero': 0003,
            'data_credito_debito':fields.Datetime.from_string('2016-02-22 00:00:00'),
            'conta_id':self.env.ref('finan.financial_account_101001').id,
            'data_pagamento':fields.Datetime.from_string('2016-02-22 00:00:00'),
            'forma_pagamento_id':self.env.ref('finan.finan_forma_pagamento_001').id,
            'banco_id':self.env.ref('finan.finan_banco_237').id,
            'vr_documento':15.50,
            'tipo':'recebimento',
            'vr_movimentado':15.50,
            'vr_multa': 0,
            'vr_juros': 0,
            'vr_adiantado': 0,
            'vr_desconto': 0,
            'vr_tarifas': 0,
        })

    #Teste 1: Conta a pagar com state efetivo e provisório falso

    def conta_a_pagar_state_teste1(self):

        self.assertEqual(self.finan_lancamento_a_pagar.provisorio, False)
        self.assertEqual(self.finan_lancamento_a_pagar.state, 'open')

    #Teste 2: Pagamento com state efetivo e provisório falso
    def pagamento_state_teste2(self):
        self.assertEqual(self.finan_lancamento_pagamento.provisorio, False)
        self.assertEqual(self.finan_lancamento_pagamento.state, 'paid')

    #Teste 3: Saldo de dívida zerado após pagamento efetuado
    def saldo_divida_zerado_teste3(self):
        self.finan_lancamento_pagamento.divida_id = self.\
            finan_lancamento_a_pagar.id
        self.assertEqual(self.finan_lancamento_a_pagar.vr_saldo, 0)

    #Teste 4: Após saldo zerado, mudança de state para quitado
    def saldo_divida_state_teste4(self):
        self.finan_lancamento_pagamento.divida_id = self.\
            finan_lancamento_a_pagar.id
