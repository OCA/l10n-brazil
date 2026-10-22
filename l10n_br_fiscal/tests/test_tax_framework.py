# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase

from ..constants.fiscal import TAX_FRAMEWORK_SIMPLES_ALL

PIS_COFINS = ("pis", "cofins")
# Domains of the company tax definitions that follow the tax regime
REGIME_DOMAINS = ("pis", "cofins", "icms", "icmssn", "ipi")


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
        # Only one active definition for each tax group
        groups = active.mapped("tax_group_id")
        self.assertEqual(len(groups), len(active))

    def _assert_chatter(self, company, before_taxes, after_taxes):
        body = company.partner_id.message_ids[:1].body or ""
        self.assertIn("Tax regime changed", body)
        for tax in before_taxes | after_taxes:
            self.assertIn(tax.name, body)

    def _change_profit_calculation(self, company, profit_calculation):
        with Form(company) as company_form:
            company_form.profit_calculation = profit_calculation

    def test_change_profit_calculation_on_company_form(self):
        """Changing the profit calculation on the company form must save
        without errors (Tax Definition already exists / cannot delete)."""
        company = self._get_company("l10n_br_base.empresa_lucro_real", "draft")
        piscofins_cum = self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
        with Form(company) as company_form:
            company_form.profit_calculation = "presumed"
            company_form.piscofins_id = piscofins_cum
        self.assertEqual(company.profit_calculation, "presumed")
        self.assertEqual(company.piscofins_id, piscofins_cum)
        definitions = self._get_company_definitions(company, active_only=True)
        for tax in (piscofins_cum.tax_pis_id, piscofins_cum.tax_cofins_id):
            self.assertEqual(
                len(definitions.filtered(lambda d, tax=tax: d.tax_id == tax)), 1
            )
        groups = definitions.mapped("tax_group_id")
        self.assertEqual(len(groups), len(definitions))

    def test_onchange_does_not_create_tax_definitions(self):
        company = self._get_company("l10n_br_base.empresa_lucro_real", "approved")
        before = self._get_company_definitions(company)
        with Form(company) as company_form:
            company_form.profit_calculation = "presumed"
            # Nothing is recorded until the form is saved
            self.assertEqual(self._get_company_definitions(company), before)

    def _run_real_to_presumed_on_company_form(self, state):
        company = self._get_company("l10n_br_base.empresa_lucro_real", state)
        old_taxes = self._active_taxes(company, PIS_COFINS)
        issqn = self._get_company_definitions(company).filtered(
            lambda d: d.tax_group_id.tax_domain == "issqn"
        )
        piscofins = self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
        self._change_profit_calculation(company, "presumed")
        self.assertEqual(company.piscofins_id, piscofins)
        new_taxes = piscofins.tax_pis_id | piscofins.tax_cofins_id
        self._assert_audit_trail(company, old_taxes, new_taxes)
        # What was not part of the regime change is left alone
        self.assertEqual(issqn.state, state)
        self._assert_chatter(company, old_taxes, new_taxes)
        # Back to the previous regime, and again: no errors
        self._change_profit_calculation(company, "real")
        self._change_profit_calculation(company, "presumed")
        self._assert_audit_trail(company, old_taxes, new_taxes)

    def test_real_to_presumed_on_company_form_draft(self):
        self._run_real_to_presumed_on_company_form("draft")

    def test_real_to_presumed_on_company_form_approved(self):
        self._run_real_to_presumed_on_company_form("approved")

    def _run_presumed_to_real_on_company_form(self, state):
        company = self._get_company("l10n_br_base.empresa_lucro_presumido", state)
        old_taxes = self._active_taxes(company, PIS_COFINS)
        piscofins = self.env.ref("l10n_br_fiscal.tax_pis_cofins_nao_columativo")
        self._change_profit_calculation(company, "real")
        new_taxes = piscofins.tax_pis_id | piscofins.tax_cofins_id
        self._assert_audit_trail(company, old_taxes, new_taxes)
        self._assert_chatter(company, old_taxes, new_taxes)

    def test_presumed_to_real_on_company_form_draft(self):
        self._run_presumed_to_real_on_company_form("draft")

    def test_presumed_to_real_on_company_form_approved(self):
        self._run_presumed_to_real_on_company_form("approved")

    def _run_simples_to_normal_and_back_on_company_form(self, state):
        company = self._get_company("l10n_br_base.empresa_simples_nacional", state)
        simples_taxes = self._active_taxes(company, REGIME_DOMAINS)
        regulation = self.env["l10n_br_fiscal.icms.regulation"].search([])[:1]
        with Form(company) as company_form:
            company_form.tax_framework = "3"
            company_form.icms_regulation_id = regulation
        self.assertEqual(company.tax_framework, "3")
        self.assertFalse(company.tax_icms_id)
        piscofins = self.env.ref("l10n_br_fiscal.tax_pis_cofins_columativo")
        normal_taxes = piscofins.tax_pis_id | piscofins.tax_cofins_id
        self._assert_audit_trail(company, simples_taxes, normal_taxes)
        self.assertFalse(
            self._active_taxes(company).filtered(lambda t: t.tax_domain == "icmssn")
        )
        self._assert_chatter(company, simples_taxes, normal_taxes)
        with Form(company) as company_form:
            company_form.tax_framework = "1"
        self.assertEqual(company.tax_framework, "1")
        sn_icms = self.env.ref("l10n_br_fiscal.tax_icms_sn_com_credito")
        self.assertIn(sn_icms, self._active_taxes(company))
        self.assertFalse(
            self._active_taxes(company).filtered(
                lambda t: t.tax_domain in ("pis", "cofins") and t in normal_taxes
            )
        )

    def test_simples_to_normal_and_back_on_company_form_draft(self):
        self._run_simples_to_normal_and_back_on_company_form("draft")

    def test_simples_to_normal_and_back_on_company_form_approved(self):
        self._run_simples_to_normal_and_back_on_company_form("approved")

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
