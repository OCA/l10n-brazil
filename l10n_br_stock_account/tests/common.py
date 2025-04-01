# Copyright (C) 2023-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.stock_picking_invoicing.tests.common import TestPickingInvoicingCommon


class TestBrPickingInvoicingCommon(TestPickingInvoicingCommon):
    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_line_onchanges(self, record):
        result = super()._run_line_onchanges(record)

        # Stock Move
        record._onchange_product_id_fiscal()
        record._onchange_fiscal_taxes()
        record._onchange_product_quantity()
        return result
