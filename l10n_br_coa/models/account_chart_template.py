# Copyright 2020 KMEE
# Copyright (C) 2025  Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging

from odoo import _, models
from odoo.tools.misc import file_open

_logger = logging.getLogger(__name__)


def _load_csv_data(filename):
    with file_open(filename, mode="r") as f:
        reader = csv.DictReader(f)
        return list(reader)


DEFAULT_TAX_ACCOUNTS = {}
for row in _load_csv_data("l10n_br_coa/data/l10n_br_coa_tax_accounts.csv"):
    DEFAULT_TAX_ACCOUNTS[row["xml_id_name_part"]] = (
        row["code_cfc"],
        row["code_itg"] or None,
        row["name"],
        row["account_type"],
    )


DEFAULT_TAX_TEMPLATES_ACCOUNTS = {}
for row in _load_csv_data("l10n_br_coa/data/l10n_br_coa_tax_templates_accounts.csv"):
    DEFAULT_TAX_TEMPLATES_ACCOUNTS[row["tax_template_xmlid"]] = (
        row["inv_rep_acc_key"],
        row["ref_rep_acc_key"],
    )


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        self.ensure_one()
        journal_data = []
        if not self.id == self.env.ref("l10n_br_coa.l10n_br_coa_template").id:
            journal_data = super()._prepare_all_journals(
                acc_template_ref, company, journals_dict
            )
        return journal_data

    def _load(self, company):
        self.ensure_one()
        result = super()._load(company)
        # Remove Company default taxes configuration
        if self.currency_id == self.env.ref("base.BRL"):
            self.env.company.write(
                {
                    "account_sale_tax_id": False,
                    "account_purchase_tax_id": False,
                }
            )
        return result

    def _load_template(
        self, company, code_digits=None, account_ref=None, taxes_ref=None
    ):
        """
        Override to write the proper tax repartion lines with a proper account_id.

        It will use the tax_group_id of the account.tax records and read the
        repartion information from the corresponding
        l10n_br_coa.account.tax.group.account.template records.
        """

        self.ensure_one()
        account_ref, taxes_ref = super()._load_template(
            company, code_digits, account_ref, taxes_ref
        )

        if self.parent_id.id == self.env.ref("l10n_br_coa.l10n_br_coa_template").id:
            self.generate_journals(account_ref, company)

        if self.parent_id and self.parent_id == self.env.ref(
            "l10n_br_coa.l10n_br_coa_template"
        ):
            # for some reason, account_ref keys can be either account ids
            # either account records. In order to match them later we ensure
            # here keys are ids:
            account_ref = {
                k.id if hasattr(k, "id") else k: v for k, v in account_ref.items()
            }

            acc_names = {
                "sale": {
                    "account_id": "account_id",
                    "refund_account_id": "refund_account_id",
                },
                "purchase": {
                    "account_id": "refund_account_id",
                    "refund_account_id": "account_id",
                },
                "all": {
                    "account_id": "account_id",
                    "refund_account_id": "refund_account_id",
                },
            }

            for tax in taxes_ref.values():
                domain = [
                    ("tax_group_id", "=", tax.tax_group_id.id),
                    ("chart_template_id", "=", self.id),
                ]
                group_tax_account_template = self.env[
                    "l10n_br_coa.account.tax.group.account.template"
                ].search(domain)
                if group_tax_account_template:
                    if tax.deductible:
                        account = group_tax_account_template.ded_account_id
                        refund_account = (
                            group_tax_account_template.ded_refund_account_id
                        )
                    elif tax.withholdable:
                        if tax.type_tax_use == "purchase":
                            account = group_tax_account_template.account_id
                            refund_account = (
                                group_tax_account_template.refund_account_id
                            )
                        else:
                            account = False
                            refund_account = False
                    else:
                        account = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("account_id")
                        ]
                        refund_account = group_tax_account_template[
                            acc_names.get(tax.type_tax_use, {}).get("refund_account_id")
                        ]

                    account_id = account_ref[account.id].id if account else False
                    refund_account_id = (
                        account_ref[refund_account.id].id if refund_account else False
                    )
                    tax._update_repartition_lines(account_id, refund_account_id)

        return account_ref, taxes_ref

    def _populate_default_br_tax_accounts(
        self, company, flavor="cfc", review_suffix=".GEN"
    ):
        """
        Populate a default Brazilian tax accounts and configure tax repartition lines.
        """
        self.ensure_one()
        Account = self.env["account.account"]
        IrModelData = self.env["ir.model.data"].sudo()
        created_accounts_refs = {}

        # 1. Create or find accounts and their XMLIDs
        for xml_id_name_part, (
            code_cfc,
            code_itg,
            name,
            acc_type,
        ) in DEFAULT_TAX_ACCOUNTS.items():
            # Use fixed codes. Ensure they don't clash with base CoA or handle it.
            # We assume these codes are specific enough.
            code = code_cfc if flavor == "cfc" else code_itg
            code = f"{code}{review_suffix}"

            # TODO: would be better to 1st search for the taxes related to all templates
            # DEFAULT_TAX_TEMPLATES_ACCOUNTS.items()
            # and if xml_id_name_part is related to a tax template for which the tax
            # repartion_line_ids have accounts already, then skip account creation
            existing_account = Account.search(
                [("code", "=", code), ("company_id", "=", company.id)], limit=1
            )
            if not existing_account:
                account = Account.create(
                    {
                        "code": code,
                        "name": name,
                        "account_type": acc_type,
                        "company_id": company.id,
                    }
                )
            else:
                account = existing_account
                # Ensure account type and reconcile status match for tests
                if account.account_type != acc_type:
                    account.write({"account_type": acc_type})

            created_accounts_refs[xml_id_name_part] = account

            # Ensure ir.model.data exists for easy reference
            tpl_ref = self.get_external_id().get(self.id)
            imd_module = tpl_ref.split(".")[0]
            imd_name = f"{company.id}_{xml_id_name_part}"
            imd_domain = [
                ("module", "=", imd_module),
                ("name", "=", imd_name),
            ]
            existing_imd = IrModelData.search(imd_domain)
            if existing_imd:
                if (
                    existing_imd.res_id != account.id
                    or existing_imd.model != "account.account"
                ):
                    existing_imd.unlink()
                    IrModelData.create(
                        {
                            "name": imd_name,
                            "module": imd_module,
                            "model": "account.account",
                            "res_id": account.id,
                            "noupdate": True,
                        }
                    )
            else:
                IrModelData.create(
                    {
                        "name": imd_name,
                        "module": imd_module,
                        "model": "account.account",
                        "res_id": account.id,
                        "noupdate": True,
                    }
                )

        # 2. Link these accounts to the account.tax records' repartition lines
        for (
            tax_template_xmlid,
            acc_mapping_keys,
        ) in DEFAULT_TAX_TEMPLATES_ACCOUNTS.items():
            tax_xmlid = f"account.{company.id}_{tax_template_xmlid.split('.')[1]}"
            company_tax = self.env.ref(tax_xmlid, raise_if_not_found=False)
            if not company_tax:
                _logger.warning(f"tax {tax_xmlid} not found! Skipping it...")
                continue

            inv_rep_acc_key, ref_rep_acc_key = acc_mapping_keys
            invoice_account = (
                created_accounts_refs.get(inv_rep_acc_key) if inv_rep_acc_key else False
            )
            refund_account = (
                created_accounts_refs.get(ref_rep_acc_key) if ref_rep_acc_key else False
            )
            company_tax._update_repartition_lines(invoice_account.id, refund_account.id)

        # Set default company accounts
        company.account_sale_tax_id = None
        company.account_purchase_tax_id = None

        _logger.info(
            _(
                "Company %(company_name)s: created tax accounts: %(refs)s",
                company_name=company.name,
                refs=created_accounts_refs,
            )
        )
        return created_accounts_refs
