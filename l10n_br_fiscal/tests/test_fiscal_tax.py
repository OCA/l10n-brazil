# Copyright 2020 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestFiscalTax(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.company_normal = self.env.ref('empresa_lucro_presumido')
        self.company_simples = self.env.ref('empresa_simples_nacional')

        self._switch_user_company(self.env.user, self.company_normal)

    def _switch_user_company(self, user, company):
        """ Add a company to the user's allowed & set to current. """
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )
