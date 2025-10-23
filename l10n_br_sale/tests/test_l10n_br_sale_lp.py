from odoo.tests import TransactionCase

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSale(L10nBrSaleBaseTest, TransactionCase):
    __test__ = True

    company_ref = "l10n_br_base.empresa_lucro_presumido"
    so_products_ref = "l10n_br_sale.lc_so_only_products"
    so_services_ref = "l10n_br_sale.lc_so_only_services"
    so_product_service_ref = "l10n_br_sale.lc_so_product_service"
