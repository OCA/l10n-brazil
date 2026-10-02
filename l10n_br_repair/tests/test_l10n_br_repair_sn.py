# Copyright 2018 Akretion - www.akretion.com.br - Magno Costa <magno.costa@akretion.com
# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged

from .test_l10n_br_repair import L10nBrRepairBaseTest


@tagged("post_install", "-at_install")
class TestL10nBrRepairSN(L10nBrRepairBaseTest, TransactionCase):
    __test__ = True

    company_ref = "l10n_br_base.empresa_simples_nacional"
    so_products_ref = "l10n_br_repair.sn_so_only_products"
    so_services_ref = "l10n_br_repair.sn_so_only_services"
    so_prod_srv_ref = "l10n_br_repair.sn_so_product_service"
