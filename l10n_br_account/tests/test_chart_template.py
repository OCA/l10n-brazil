# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestChartTemplate(TransactionCase):
    def test_br_oca_journals_do_not_use_latam_documents(self):
        if "l10n_latam_use_documents" not in self.env["account.journal"]._fields:
            self.skipTest("l10n_latam_invoice_document is not installed")
        company = self.env["res.company"].create(
            {
                "name": "Empresa nova",
                "country_id": self.env.ref("base.br").id,
                "currency_id": self.env.ref("base.BRL").id,
            }
        )
        self.env["account.chart.template"].try_loading("br_oca", company)
        journals = self.env["account.journal"].search(
            [("company_id", "=", company.id), ("type", "in", ("sale", "purchase"))]
        )
        self.assertTrue(journals)
        self.assertFalse(any(journals.mapped("l10n_latam_use_documents")))
