# Copyright 2018 Akretion - www.akretion.com.br - Magno Costa <magno.costa@akretion.com
# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .test_l10n_br_repair import L10nBrRepairBaseTest


class TestL10nBrRepairSN(L10nBrRepairBaseTest):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('l10n_br_base.empresa_simples_nacional')
        self.so_products = self.env.ref('l10n_br_repair.sn_so_only_products')
        self.so_services = self.env.ref('l10n_br_repair.sn_so_only_services')
        self.so_prod_srv = self.env.ref('l10n_br_repair.sn_so_product_service')
