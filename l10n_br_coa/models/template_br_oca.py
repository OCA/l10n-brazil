# Copyright 2020 KMEE
# Copyright (C) 2025  Raphaël Valyi - Akretion
# Copyright 2025 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging

from odoo import Command, _, api, models
from odoo.tools.misc import file_open

from odoo.addons.account.models.chart_template import template

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


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("br_oca")
    def _get_br_oca_template_data(self):
        return {
            "name": _("Plano de Contas Base"),
            "visible": True,  # TODO
            "code_digits": "2",
            "use_anglo_saxon": True,
        }

    @template("br_oca", "account.tax.group")
    def _get_br_oca_tax_group_data(self):
        csv_path = "l10n_br_coa/data/template/account.tax.group-br_oca.csv"
        data = {}
        for row in _load_csv_data(csv_path):
            data[row["id"]] = {"name": row["name"]}
        return data

    @template("br_oca", "account.tax")
    def _get_br_oca_tax_data(self):
        csv_path = "l10n_br_coa/data/template/account.tax-br_oca.csv"
        data = {}
        for row in _load_csv_data(csv_path):
            vals = {
                "name": row["name"],
                "description": row["description"],
                "amount": float(row["amount"]),
                "amount_type": "percent",
                "type_tax_use": row["type_tax_use"],
                "price_include": row["price_include"] == "1",
                "tax_group_id": row["tax_group_id"],
            }
            if "deductible" in row:
                vals["deductible"] = row["deductible"] == "1"
            if "withholdable" in row:
                vals["withholdable"] = row["withholdable"] == "1"
            data[row["id"]] = vals
        return data

    @template("br_oca", "res.company")
    def _get_br_oca_res_company(self):
        return {
            self.env.company.id: {
                "account_fiscal_country_id": "base.br",
                "cash_account_code_prefix": "1.1.1.1.",
                "bank_account_code_prefix": "1.1.1.2.",
                "transfer_account_code_prefix": "1.1.1.2.0",
                "account_sale_tax_id": False,
                "account_purchase_tax_id": False,
            },
        }

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        self.ensure_one()
        journal_data = []
        if not self.id == self.env.ref("l10n_br_coa.l10n_br_coa_template").id:
            journal_data = super()._prepare_all_journals(
                acc_template_ref, company, journals_dict
            )
        return journal_data

    def _load(self, template_code, company, install_demo):
        result = super()._load(template_code, company, install_demo)
        # Remove Company default taxes configuration
        if company.currency_id == self.env.ref("base.BRL"):
            company.write(
                {
                    "account_sale_tax_id": False,
                    "account_purchase_tax_id": False,
                }
            )
        return result

    def _set_tax_group_accs(self, template_code, tax_data):
        group_to_accounts = self._get_tax_group_accounts(template_code)
        for tax in tax_data.values():
            if (
                tax.get("tax_group_id") not in group_to_accounts
                or tax.get("type_tax_use") not in ("sale", "purchase", "all")
                or tax.get("repartition_line_ids")
            ):
                continue
            accs = group_to_accounts[tax["tax_group_id"]]
            if tax.get("deductible"):
                account_id = accs.get("ded_account_id", False)
                refund_account_id = accs.get("ded_refund_account_id", False)
            elif tax.get("withholdable") and tax["type_tax_use"] != "purchase":
                account_id = False
                refund_account_id = False
            else:
                account_id = accs.get("account_id", False)
                refund_account_id = accs.get("refund_account_id", False)
                if not tax.get("withholdable") and tax["type_tax_use"] == "purchase":
                    account_id, refund_account_id = refund_account_id, account_id

            for fname in (
                "invoice_repartition_line_ids",
                "refund_repartition_line_ids",
            ):
                if not tax.get(fname):
                    tax[fname] = [
                        Command.create({"repartition_type": "base"}),
                        Command.create({"repartition_type": "tax"}),
                    ]
                is_refund = fname == "refund_repartition_line_ids"
                for _command, _id, repartition in tax[fname]:
                    repartition["account_id"] = (
                        refund_account_id if is_refund else account_id
                    )
                    repartition["factor_percent"] = (
                        -1 if tax.get("deductible") or tax.get("withholdable") else 1
                    ) * 100

    def _get_tax_group_accounts(self, template_code):
        """
        Default invoice/refund accounts by tax group
        Data previously populated l10n_br_coa.account.tax.group.account.template
        until v16, when CoA template models was used

        [tax_group_id xmlid (pseudo)]: {
            ded_account_id: xmlid
            ded_refund_account_id: xmlid
            account_id: xmlid
            refund_account_id: xmlid
        }
        """
        return dict()

    @api.model
    def _populate_default_br_tax_accounts(
        self, company, flavor="cfc", review_suffix=".GEN", template_module="l10n_br_coa"
    ):
        """
        Populate a default Brazilian tax accounts and configure tax repartition lines.
        """
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
            imd_module = self._get_chart_template_mapping().get(company.chart_template)[
                "module"
            ]  # FIXME sure oca_br and not other code??
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
            tax_xmlid = (
                f"{template_module}.{company.id}_{tax_template_xmlid.split('.')[1]}"
            )
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

        # Void default company sale/purchase taxes:
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
