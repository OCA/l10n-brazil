# Copyright (C) 2026  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase, tagged
from odoo.tools import SQL


@tagged("post_install", "-at_install")
class TestProxyColumnsInit(TransactionCase):
    def _init_proxy_columns(self, records, columns):
        """Proxy columns as created when installing on existing documents."""
        records.flush_recordset()
        for column in columns:
            self.env.cr.execute(
                SQL(
                    "UPDATE %s SET %s = NULL WHERE id IN %s",
                    SQL.identifier(records._table),
                    SQL.identifier(column),
                    tuple(records.ids),
                )
            )
            records._init_column(column)
        records.invalidate_recordset()

    def test_proxy_columns_init(self):
        document = self.env.ref("l10n_br_fiscal.demo_nfe_same_state")
        line = document.fiscal_line_ids[0]
        self._init_proxy_columns(document, ["proxy_company_id", "proxy_partner_id"])
        self._init_proxy_columns(line, list(line._proxy_shadowed_columns))

        self.assertEqual(document.proxy_company_id, document.company_id)
        self.assertEqual(document.proxy_partner_id, document.partner_id)
        self.assertEqual(line.proxy_product_id, line.product_id)
        self.assertEqual(line.proxy_quantity, line.quantity)
        self.assertEqual(document.copy().company_id, document.company_id)

        product = self.env.ref("product.product_product_7")
        line.product_id = product
        self.assertEqual(line.name, product.display_name)
