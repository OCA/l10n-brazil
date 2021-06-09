# Copyright (C) 2016  Magno Costa - Akretion
# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleLC(L10nBrSaleBaseTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.so_products = cls.env.ref("l10n_br_sale.lc_so_only_products")
        cls.so_services = cls.env.ref("l10n_br_sale.lc_so_only_services")
        cls.so_prod_srv = cls.env.ref("l10n_br_sale.lc_so_product_service")
