# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from ..tools.misc import punctuation_rm, calc_price_ratio
from odoo.tests.common import TransactionCase


class Tests(TransactionCase):

    def test_punctution_rm(self):
        self.assertEquals(
            punctuation_rm('496.85994.95-7'), '49685994957',
            'The function punctuation_rm failed.')

    def test_calc_price_ratio(self):
        self.assertEquals(
            calc_price_ratio(10, 100, 1000), 1.0,
            'The function calc_price_ratio failed.')
        self.assertEquals(
            calc_price_ratio(10, 100, 0), 0,
            'The function calc_price_ratio failed.')
