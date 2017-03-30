# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.addons.sped.constante_tributaria import *

class TestAccountMoveTemplate(TransactionCase):

    def setUp(self):
        super(TestAccountMoveTemplate, self).setUp()
        self.amt = self.env['account.move.template.rule']
        self.main_company = self.env.ref('base.main_company')
        self.fiscal_document_service = self.env.ref(
            'l10n_br_account.fiscal_document_service')
        self.fiscal_document_55 = self.env[
            'l10n_br_account.fiscal.document'].create(
            dict(code=u'55', name=u'Nota fiscal eletronica', electronic=True)
        )

    def test_map_account_01(self):
        """ DADO uma operação de revenda para dentro do estado
            E um produto nacional
            E pagamento a vista
            E um lançamento do tipo
        QUANDO for efetuar um lançamento contábil

        ENTÂO devera ser efetuado um **credito** na conta de clientes
            E **debito** na conta de receita de revenda no mercado interno
        :return:
        """
        kwargs = {
            'company_id': self.main_company,
            'fiscal_document_id': self.fiscal_document_55,
            'account_type': 'receita',
            'operation_nature': 'revenda',
            'operation_position': 'dentro_estado',
            'product_type': 'mercadoria_revenda',
            'product_origin': 'nacional',
            'term': 'curto',
            'account_move_type': 'receita'
        }
        debit, credit = self.amt.map_account(**kwargs)
        print (debit, credit)
