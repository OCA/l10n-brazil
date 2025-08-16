# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestServiceType(TransactionCase):
    def test_display_name(self):
        self.service_type = self.env["l10n_br_fiscal.service.type"].create(
            {"code": "TESTE", "name": "TESTE", "internal_type": "normal"}
        )
        self.assertEqual(self.service_type.display_name, "TESTE - TESTE")
