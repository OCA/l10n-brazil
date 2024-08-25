# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleSN(L10nBrSaleBaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.so_products = cls.env.ref("l10n_br_sale.sn_so_only_products")
        cls.so_services = cls.env.ref("l10n_br_sale.sn_so_only_services")
        cls.so_product_service = cls.env.ref("l10n_br_sale.sn_so_product_service")
