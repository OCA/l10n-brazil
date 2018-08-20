# -*- coding: utf-8 -*-
# @ 2016 KMEE - www.kmee.com.br -
#   Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from ..tools.fiscal import validate_pis_pasep
from odoo.tests.common import TransactionCase


class Tests(TransactionCase):

    def test_01_validate_pis_pasep(self):
        self.assertTrue(validate_pis_pasep('496.85994.95-6'))

    def test_02_validate_pis_pasep(self):
        self.assertFalse(validate_pis_pasep('496.85994.95-7'))
