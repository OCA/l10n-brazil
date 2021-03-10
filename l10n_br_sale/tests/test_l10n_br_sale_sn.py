# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleSN(L10nBrSaleBaseTest):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.company = self.env.ref('l10n_br_base.empresa_simples_nacional')
        self.so_products = self.env.ref('l10n_br_sale.sn_so_only_products')
        self.so_services = self.env.ref('l10n_br_sale.sn_so_only_services')
        self.so_prod_srv = self.env.ref('l10n_br_sale.sn_so_product_service')
