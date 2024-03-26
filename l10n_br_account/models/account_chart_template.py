# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _load(self, company):
        """
        Avoid to populate account_sale/purchase_tax_id
        with tax that cannot be applied in Brazil and confuses the users.
        """
        res = super()._load(company)
        if self.parent_id and self.parent_id == self.env.ref(
            "l10n_br_coa.l10n_br_coa_template"
        ):
            company.account_sale_tax_id = None
            company.account_purchase_tax_id = None
        return res

    def _load_template(
        self, company, code_digits=None, account_ref=None, taxes_ref=None
    ):
        """
        If the CoA is installed before l10n_br_account, at least we trigger
        load_fiscal_taxes from the l10n_br_account/hooks.py for the demo CoA's.
        With this override, we also ensure these demo CoA or any custom CoA
        will get its account taxes properly linked to fiscal taxes when it is
        installed after l10n_br_account.
        """
        self.ensure_one()
        account_ref, taxes_ref = super()._load_template(
            company, code_digits, account_ref, taxes_ref
        )

        if self.parent_id and self.parent_id == self.env.ref(
            "l10n_br_coa.l10n_br_coa_template"
        ):
            self.load_fiscal_taxes()
        return account_ref, taxes_ref

    def load_fiscal_taxes(self):
        """
        Relate account taxes with fiscal taxes to enable the Brazilian
        tax engine to kick in with the installed chart of account.
        """
        for coa_tpl in self:
            companies = self.env["res.company"].search(
                [("chart_template_id", "=", coa_tpl.id)]
            )

            for company in companies:
                taxes = self.env["account.tax"].search(
                    [("company_id", "=", company.id)]
                )

                for tax in taxes:
                    if tax.get_external_id():
                        tax_ref = tax.get_external_id().get(tax.id)
                        ref_module, ref_name = tax_ref.split(".")
                        ref_name = ref_name.replace(str(company.id) + "_", "")
                        template_source_ref = ".".join(["l10n_br_coa", ref_name])
                        template_source = self.env.ref(template_source_ref)
                        tax_source_ref = ".".join([ref_module, ref_name])
                        tax_template = self.env.ref(tax_source_ref)
                        tax.fiscal_tax_ids = (
                            tax_template.fiscal_tax_ids
                        ) = template_source.fiscal_tax_ids
