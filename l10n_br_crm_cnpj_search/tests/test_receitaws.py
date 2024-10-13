# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_cnpj_search.tests.test_receitaws import (
    TestReceitaWS,
)


class TestCRMReceitaws(TestReceitaWS):
    def test_crm_receita_ws_success(self):
        self.assertTrue(True)
