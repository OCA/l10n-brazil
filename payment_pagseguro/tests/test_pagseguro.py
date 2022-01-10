# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import odoo
from odoo.tests.common import HttpCase

_logger = logging.getLogger(__name__)


@odoo.tests.tagged("post_install", "-at_install")
class PagseguroTest(HttpCase):
        
    def test_buy_with_pagseguro(self):
        self.phantom_js("/", "odoo.__DEBUG__.services['web_tour.tour'].run('shop_buy_with_pagseguro')", "odoo.__DEBUG__.services['web_tour.tour'].tours.shop_buy_with_pagseguro.ready", login="admin")
