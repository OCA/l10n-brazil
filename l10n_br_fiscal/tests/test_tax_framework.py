# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

PIS_COFINS = ("pis", "cofins")


class TestTaxFramework(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company

    def test_mei_is_simples_nacional_all(self):
        self.assertIn("4", TAX_FRAMEWORK_SIMPLES_ALL)

    def test_mei_gets_simples_nacional_taxes_onchange(self):
        self.company.tax_framework = "4"
        self.company._onchange_profit_calculation()
        self.assertEqual(
            self.company.tax_icms_id,
            self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito"),
        )
        self.assertEqual(
            self.company.piscofins_id,
            self.env.ref("l10n_br_fiscal.tax_pis_cofins_simples_nacional"),
        )

    def _get_company_definitions(self, company, active_only=False):
        domain = [("company_id", "=", company.id)]
        if active_only:
            domain.append(("state", "!=", "expired"))
        return self.env["l10n_br_fiscal.tax.definition"].search(domain)

    def _get_company(self, xmlid, state):
        company = self.env.ref(xmlid)
        self.env.user.company_ids |= company
        self.env.user.groups_id |= self.env.ref("l10n_br_fiscal.group_manager")
        self._get_company_definitions(company).write({"state": state})
        return company

    def _active_taxes(self, company, tax_domains=None):
        definitions = self._get_company_definitions(company, active_only=True)
        if tax_domains:
            definitions = definitions.filtered(
                lambda d: d.tax_group_id.tax_domain in tax_domains
            )
        return definitions.mapped("tax_id")

    def _assert_audit_trail(self, company, old_taxes, new_taxes):
        """The old definitions stay as history, the new ones start now."""
        definitions = self._get_company_definitions(company)
        active = definitions.filtered(lambda d: d.state != "expired")
        expired = definitions.filtered(lambda d: d.state == "expired")
        for tax in new_taxes:
            self.assertEqual(
                len(active.filtered(lambda d, tax=tax: d.tax_id == tax)),
                1,
                tax.name,
            )
        for tax in old_taxes - new_taxes:
            self.assertFalse(active.filtered(lambda d, tax=tax: d.tax_id == tax))
            old = expired.filtered(lambda d, tax=tax: d.tax_id == tax)
            self.assertTrue(old, tax.name)
            self.assertTrue(all(d.date_end for d in old))
        for definition in active.filtered(lambda d: d.tax_id in new_taxes):
            if definition.tax_id not in old_taxes:
                self.assertTrue(definition.date_start)
        # Only one generic active definition for each tax group
        generic = active.filtered(lambda d: not d.ncm_ids)
        self.assertEqual(len(generic.mapped("tax_group_id")), len(generic))

    def _change_profit_calculation(self, company, profit_calculation):
        with Form(company) as company_form:
            company_form.profit_calculation = profit_calculation

    def _run_real_to_presumed_on_company_form(self, state):
        company = self._get_company("l10n_br_base.empresa_lucro_real", state)
        old_taxes = self._active_taxes(company, PIS_COFINS)
        issqn = self._get_company_definitions(company).filtered(
            lambda d: d.tax_group_id.tax_domain == "issqn"
        )
        # A definition restricted to a NCM was set up by hand: it is kept
        pis_0 = self.env.ref("l10n_br_fiscal.tax_pis_0")
        pis_ncm = self.env["l10n_br_fiscal.tax.definition"].create(
            {
                "type_in_out": "out",
                "tax_group_id": pis_0.tax_group_id.id,
                "custom_tax": True,
                "tax_id": pis_0.id,
                "cst_id": pis_0.cst_out_id.id,
                "company_id": company.id,
                "ncm_ids": [
                    Command.set(self.env.ref("l10n_br_fiscal.ncm_48191000").ids)
                ],
            }
        )
        pis_ncm.state = state
        piscofins = self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
        self._change_profit_calculation(company, "presumed")
        self.assertEqual(company.piscofins_id, piscofins)
        new_taxes = piscofins.tax_pis_id | piscofins.tax_cofins_id
        self._assert_audit_trail(company, old_taxes, new_taxes)
        # What was not part of the regime change is left alone
        self.assertEqual(issqn.state, state)
        self.assertEqual(pis_ncm.state, state)

    def test_real_to_presumed_on_company_form_draft(self):
        self._run_real_to_presumed_on_company_form("draft")

    def test_real_to_presumed_on_company_form_approved(self):
        self._run_real_to_presumed_on_company_form("approved")

    def test_expired_definition_does_not_block_a_new_one(self):
        company = self._get_company("l10n_br_base.empresa_lucro_real", "approved")
        definition = self._get_company_definitions(company)[:1]
        definition.write({"state": "expired", "date_end": "2020-01-01 00:00:00"})
        duplicated = definition.copy(
            {"company_id": company.id, "state": "draft", "date_end": False}
        )
        self.assertEqual(duplicated.state, "draft")
        with self.assertRaises(ValidationError):
            definition.copy({"company_id": company.id, "state": "approved"})

    def _get_user_without_fiscal_group(self):
        """Internal user that manages companies but has no fiscal group."""
        return self.env["res.users"].create(
            {
                "name": "User without fiscal group",
                "login": "user_without_fiscal_group",
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("base.group_erp_manager").id,
                            self.env.ref("base.group_partner_manager").id,
                        ]
                    )
                ],
            }
        )

    def test_user_without_fiscal_group_changes_tax_regime(self):
        user = self._get_user_without_fiscal_group()
        company = self._get_company("l10n_br_base.empresa_lucro_real", "approved")
        user.company_ids |= company
        piscofins = self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
        company.with_user(user).write(
            {"profit_calculation": "presumed", "piscofins_id": piscofins.id}
        )
        self.assertEqual(
            self._active_taxes(company, PIS_COFINS),
            piscofins.tax_pis_id | piscofins.tax_cofins_id,
        )
        messages = company.partner_id.sudo().message_ids
        self.assertIn("Tax regime changed", " ".join(messages.mapped("body")))
