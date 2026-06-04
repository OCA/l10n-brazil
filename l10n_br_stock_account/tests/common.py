# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.stock_picking_invoicing.tests.common import (
    TestStockPickingInvoicingCommon,
)
from odoo.addons.stock_picking_invoicing.tests.tools import (
    create_with_form_inv_onshipping,
    create_with_form_pck_backorder,
    create_with_form_return_picking,
)


class TestBrPickingInvoicingCommon(TestStockPickingInvoicingCommon):
    chart_template = "generic_coa"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Add main company to test user to access demo data from other modules
        main_company = cls.env.ref("base.main_company")
        cls.env.user.company_ids |= main_company

    @classmethod
    def get_default_groups(cls):
        groups = super().get_default_groups()
        return (
            groups
            | cls.env.ref("l10n_br_fiscal.group_user")
            | cls.env.ref("l10n_br_fiscal.group_manager")
            | cls.env.ref("stock.group_stock_manager")
        )

    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_picking_onchanges(self, record):
        """Run picking onchanges (compatibility with 17.0 tests)."""
        record._onchange_invoice_state()

    def create_invoice_wizard(self, pickings):
        return create_with_form_inv_onshipping(self.env, pickings)

    def return_picking_wizard(self, picking):
        return create_with_form_return_picking(self.env, picking)

    def create_backorder_wizard(self, picking):
        return create_with_form_pck_backorder(self.env, picking)
