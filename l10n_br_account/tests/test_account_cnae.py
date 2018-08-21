# -*- coding: utf-8 -*-
# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestAccountCNAE(TransactionCase):
    def test_name_get(self):
        self.account_cnae = self.env[
            'l10n_br_account.cnae'].create(dict(
                code='TESTE',
                name='TESTE',
                version='TESTE',
                internal_type='normal',))
        assert self.account_cnae.name_get(), \
            'Error with function name_get() of object l10n_br_account.cnae'
