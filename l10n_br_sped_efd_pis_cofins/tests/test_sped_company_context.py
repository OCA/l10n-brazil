# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon


@tagged("post_install", "-at_install")
class TestSpedEfdPisCofinsCompanyContext(SpedEntradaCommon):
    """The declaration runs as its own company, whatever the active one is."""

    KIND = "efd_pis_cofins"

    def _user(self, companies):
        other = self.env.ref("base.main_company")
        self.assertNotEqual(other, self.company)
        return self.env["res.users"].create(
            {
                "name": "Fiscal of another company",
                "email": "fiscal.other@example.com",
                "login": "fiscal_other_company_efd_pis_cofins",
                "company_id": other.id,
                "company_ids": [(6, 0, companies.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_manager").id,
                            self.env.ref("account.group_account_manager").id,
                            self.env.ref("stock.group_stock_user").id,
                        ],
                    )
                ],
            }
        )

    def _declaration_of_the_company(self, user):
        """The user has another company active and declares for self.company."""
        env = self.env(
            user=user.id,
            context=dict(self.env.context, allowed_company_ids=[user.company_id.id]),
        )
        env["l10n_br_sped.mixin"]._flush_registers(self.KIND)
        declaration = env[f"l10n_br_sped.{self.KIND}.0000"].create(
            {
                "company_id": self.company.id,
                "DT_INI": date(2026, 7, 1),
                "DT_FIN": date(2026, 7, 31),
            }
        )
        return declaration

    def test_the_company_not_active_in_the_session_is_not_empty(self):
        self._entry_document()
        user = self._user(self.env.ref("base.main_company") | self.company)
        declaration = self._declaration_of_the_company(user)
        declaration.button_populate_sped_from_odoo()
        text = declaration._generate_sped_text()
        self.assertIn("|C100|", text)
        self.assertIn("|0150|", text)

    def test_a_user_without_access_to_the_company_gets_a_clear_error(self):
        self._entry_document()
        user = self._user(self.env.ref("base.main_company"))
        declaration = self._declaration_of_the_company(user)
        with self.assertRaisesRegex(UserError, "no access to the company"):
            declaration.button_populate_sped_from_odoo()
        with self.assertRaisesRegex(UserError, "no access to the company"):
            declaration._generate_sped_text()
