# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
#   Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSaleSN(L10nBrSaleBaseTest, TransactionCase):
    __test__ = True

    # Odoo 19 only collects the test methods defined in the class itself
    # (see odoo/tests/loader.py), so opt in to keep the tests inherited from
    # the shared L10nBrSaleBaseTest base class.
    allow_inherited_tests_method = True

    company_ref = "l10n_br_base.empresa_simples_nacional"
    so_products_ref = "l10n_br_sale.sn_so_only_products"
    so_services_ref = "l10n_br_sale.sn_so_only_services"
    so_product_service_ref = "l10n_br_sale.sn_so_product_service"
