# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_l10n_br_purchase_stock import L10nBrPurchaseStockBase


class L10nBrPurchaseStockBase(L10nBrPurchaseStockBase):
    def setUp(self):
        super().setUp()
