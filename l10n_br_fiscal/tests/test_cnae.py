# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestCNAE(TransactionCase):
    def test_display_name(self):
        self.cnae = self.env["l10n_br_fiscal.cnae"].create(
            {
                "code": "TESTE",
                "name": "TESTE",
                "version": "TESTE",
                "internal_type": "normal",
            }
        )
        self.assertEqual(self.cnae.display_name, "TESTE - TESTE")
