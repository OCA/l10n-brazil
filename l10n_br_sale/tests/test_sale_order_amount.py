from odoo.tests import TransactionCase
from odoo.tests.common import tagged

from .tools import load_sale_fixture_files


@tagged("post_install", "-at_install")
class TestSaleOrderAmount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Load demo data as fixtures if not already present: OCA CI installs
        # the modules without demo data, and this test refs the demo company,
        # partner and product records.
        if not cls.env.ref(
            "l10n_br_sale.main_so_only_products", raise_if_not_found=False
        ):
            load_sale_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        # FURN_8855 has IPI, a tax not included in the price
        cls.product = cls.env.ref("product.product_product_27")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
