# Copyright 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestFiscalTaxWithoutChart(TransactionCase):
    """Creating a fiscal tax creates the matching account taxes in the tax
    group linked to its fiscal tax group. Without such a group (no chart of
    accounts installed with it), there is nothing to create, and the fiscal
    tax must still be created (e.g. on the fly by an NF-e import)."""

    def test_create_fiscal_tax_without_account_tax_group(self):
        tax_group = self.env["l10n_br_fiscal.tax.group"].create(
            {
                "name": "Test group without account tax group",
                "tax_scope": "other",
                "tax_domain": "others",
            }
        )
        self.assertFalse(tax_group.account_tax_group())
        # copy() goes through create(), as the import does
        fiscal_tax = self.env.ref("l10n_br_fiscal.tax_pis_0_65").copy(
            {
                "name": "Test tax without account tax group",
                "tax_group_id": tax_group.id,
            }
        )
        self.assertTrue(fiscal_tax)
        self.assertFalse(
            self.env["account.tax"].search([("fiscal_tax_ids", "in", fiscal_tax.ids)])
        )
