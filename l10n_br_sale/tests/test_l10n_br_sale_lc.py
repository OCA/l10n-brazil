# Copyright (C) 2016  Magno Costa - Akretion
# Copyright (C) 2020  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleLC(L10nBrSaleBaseTest):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('l10n_br_base.empresa_lucro_presumido')
        self.so_products = self.env.ref('l10n_br_sale.lc_so_only_products')
        self.so_services = self.env.ref('l10n_br_sale.lc_so_only_services')
        self.so_prod_srv = self.env.ref('l10n_br_sale.lc_so_product_service')
