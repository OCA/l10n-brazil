# Copyright 2020 KMEE
# Copyright (C) 2025  Raphaël Valyi - Akretion
# Copyright 2025 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv
import logging

from odoo import Command, api, models
from odoo.tools.misc import file_open
from odoo.tools.translate import _

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

    @api.model
    def _get_accounts_data_values(
        self, company, template_data, bank_prefix="", code_digits=0
    ):
        """The utility liquidity transfer account is born classified.

        The core creates it alone when loading the chart, looking for the
        first free code after the `transfer_account_code_prefix`: declaring
        it in the chart would only make the core create a second one beside
        it. Without the classification the account stays out of the reports,
        which select by tag, and a transfer between banks still in transit at
        the end of the period would show up as an unexplained difference on
        the balance sheet and the cash flow statement. It IS cash and
        equivalents: a passage account between two liquidity accounts.
        """
        vals_list = super()._get_accounts_data_values(
            company, template_data, bank_prefix=bank_prefix, code_digits=code_digits
        )
        tag = self.env.ref(
            "l10n_br_coa.account_tag_cash_and_equivalents", raise_if_not_found=False
        )
        if tag:
            transfer = vals_list.get("transfer_account_id")
            if transfer is not None:
                transfer["name"] = _("Liquidity Transfer")
                transfer["tag_ids"] = [(4, tag.id)]
        return vals_list

    @template("br_oca")
    def _get_br_oca_template_data(self):
        return {
            "name": self.env._("Basic Chart of Accounts"),
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

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(template_code, company, install_demo, force_create)
        # Remove Company default taxes configuration
        if company.currency_id == self.env.ref("base.BRL"):
            company.write(
                {
                    "account_sale_tax_id": False,
                    "account_purchase_tax_id": False,
                }
            )
            flavor = "itg"
            # `tax_framework` is a fiscal field: `l10n_br_coa` only depends on
            # `account`, so the chart load can run where l10n_br_fiscal is not
            # installed and the attribute does not exist at all.
            tax_framework = getattr(company, "tax_framework", False)
            if template_code == "br_oca_generic" or tax_framework == "3":
                flavor = "cfc"
            self._populate_default_br_tax_accounts(company, flavor=flavor)
            self._l10n_br_setup_outstanding_accounts(company)
        return result

    def _l10n_br_setup_outstanding_accounts(self, company):
        """Classify the outstanding accounts and put them on the bank journals.

        The core creates "Outstanding Receipts" and "Outstanding Payments" with
        the chart but, since Odoo 17, does not put them on the payment method
        lines, so a payment goes straight to the bank account and there is
        nothing left to reconcile with the statement. Also run by the migration
        of 18.0.3.4.0 for the companies already loaded.
        """
        chart = self.with_company(company)
        accounts = self.env["account.account"]
        for xmlid in (
            "account_journal_payment_debit_account_id",
            "account_journal_payment_credit_account_id",
        ):
            accounts |= chart.ref(xmlid, raise_if_not_found=False) or accounts
        tags = self.env["account.account.tag"]
        for xmlid in (
            "l10n_br_coa.account_tag_current_assets_cash",
            "l10n_br_coa.account_tag_cash_and_equivalents",
        ):
            tags |= self.env.ref(xmlid, raise_if_not_found=False) or tags
        if accounts and tags:
            accounts.write({"tag_ids": [Command.link(tag.id) for tag in tags]})
        self.env["account.journal"].search(
            [("company_id", "=", company.id), ("type", "in", ("bank", "cash"))]
        )._l10n_br_link_outstanding_accounts()

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
        # Track codes we've already created in this batch to handle duplicates
        # (e.g., regular and withholding tax accounts may share the same code)
        created_accounts_by_code = {}

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
            code_gen = f"{code}{review_suffix}"

            # Reuse account if same code was already processed in this loop
            # (some tax accounts share the same code in the CSV)
            if code in created_accounts_by_code:
                created_accounts_refs[xml_id_name_part] = created_accounts_by_code[code]
                continue

            # TODO: would be better to 1st search for the taxes related to all templates
            # DEFAULT_TAX_TEMPLATES_ACCOUNTS.items()
            # and if xml_id_name_part is related to a tax template for which the tax
            # repartion_line_ids have accounts already, then skip account creation
            existing_account = Account.search(
                [("code", "in", [code, code_gen]), ("company_ids", "in", [company.id])],
                limit=1,
            )
            if not existing_account:
                account = Account.create(
                    {
                        "code": code_gen,
                        "name": name,
                        "account_type": acc_type,
                        "company_ids": [Command.link(company.id)],
                    }
                )
            else:
                account = existing_account
                # Ensure account type and reconcile status match for tests
                if account.account_type != acc_type:
                    account.write({"account_type": acc_type})

            created_accounts_refs[xml_id_name_part] = account
            created_accounts_by_code[code] = account

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
                tax_xmlid = f"account.{company.id}_{tax_template_xmlid.split('.')[1]}"
                company_tax = self.env.ref(tax_xmlid, raise_if_not_found=False)

                if not company_tax:
                    _logger.info(f"tax {tax_xmlid} not found! Skipping it...")
                    continue

            inv_rep_acc_key, ref_rep_acc_key = acc_mapping_keys
            invoice_account = (
                created_accounts_refs.get(inv_rep_acc_key) if inv_rep_acc_key else False
            )
            refund_account = (
                created_accounts_refs.get(ref_rep_acc_key) if ref_rep_acc_key else False
            )
            company_tax.sudo()._update_repartition_lines(
                invoice_account.id, refund_account.id
            )

        # Void default company sale/purchase taxes:
        company.account_sale_tax_id = None
        company.account_purchase_tax_id = None

        _logger.info(
            self.env._(
                "Company %(company_name)s: created tax accounts: %(refs)s",
                company_name=company.name,
                refs=created_accounts_refs,
            )
        )
        return created_accounts_refs
