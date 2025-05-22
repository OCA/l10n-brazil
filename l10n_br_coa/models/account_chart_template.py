# Copyright 2020 KMEE
# Copyright (C) 2025  Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)

# XML ID name part will be prefixed with 'l10n_br_coa.'
DEFAULT_TAX_ACCOUNTS = {
    # xml_id_name_part: (code_cfc, code_itg, name, account_type)
    "tax_icms_payable": (
        "2.1.7.1.03",
        "2.1.3.02",
        "ICMS a Recolher",
        "liability_current",
    ),
    "tax_icms_receivable": (
        "1.1.4.1.02",
        "1.1.4.02",
        "ICMS a Compensar",
        "asset_current",
    ),
    "tax_icms_sales_revenue": (
        "6.1.1.2.03",
        "3.1.1.04",
        "ICMS s/ Vendas",
        "income_other",
    ),
    "tax_icms_purchase_expense": (
        "6.1.1.2.23",
        "3.1.1.04",
        "ICMS s/ Compras",  # TODO check tax template below
        "expense",
    ),
    "tax_ipi_payable": (
        "2.1.7.1.02",
        "2.1.3.04",
        "IPI a Recolher",
        "liability_current",
    ),
    "tax_ipi_receivable": (
        "1.1.4.1.01",
        "1.1.4.02",
        "IPI a Compensar",
        "asset_current",
    ),
    "tax_ipi_sales_revenue": (
        "6.1.1.2.08",
        "3.1.1.04",
        "IPI s/ Vendas",
        "income_other",
    ),
    "tax_ipi_purchase_expense": (
        "6.1.1.2.28",
        "3.1.1.04",
        "IPI s/ Compras",  # "(-) IPI Devolução Venda",  # FIXME!!!
        "income_other",
    ),
    "tax_pis_payable": (
        "2.1.7.1.05",
        "2.1.3.01",
        "PIS a Recolher",
        "liability_current",
    ),  # ITG: Simples Nacional or specific if not Simples
    "tax_pis_receivable": (
        "1.1.4.1.05",
        "1.1.4.02",
        "PIS a Compensar",
        "asset_current",
    ),  # ITG: General Impostos a Recuperar (2.1.3.05 is a liability in CSV)
    "tax_pis_sales_revenue": (
        "6.1.1.2.06",
        "3.1.1.04",
        "PIS s/ Vendas",
        "income_other",
    ),
    "tax_pis_purchase_expense": (
        "6.1.1.2.26",
        "3.1.1.04",
        "PIS s/ Compras",  # "(-) PIS Devolução Venda",
        "income_other",
    ),
    "tax_cofins_payable": (
        "2.1.7.1.04",
        "2.1.3.01",
        "COFINS a Recolher",
        "liability_current",
    ),  # ITG: Simples Nacional or specific if not Simples
    "tax_cofins_receivable": (
        "1.1.4.1.04",
        "1.1.4.02",
        "COFINS a Compensar",
        "asset_current",
    ),  # ITG: General Impostos a Recuperar (2.1.3.06 is a liability in CSV)
    "tax_cofins_sales_revenue": (
        "6.1.1.2.05",
        "3.1.1.04",
        "COFINS s/ Vendas",
        "income_other",
    ),
    "tax_cofins_purchase_expense": (
        "6.1.1.2.25",
        "3.1.1.04",
        "COFINS s/ Compras",  # "(-) COFINS Devolução Venda",
        "income_other",
    ),
    "tax_icmssn_payable": (
        "2.1.7.1.01",
        "2.1.3.02",
        "ICMS SN a Recolher",
        "liability_current",
    ),
    "tax_icms_st_payable": (
        "2.1.7.1.11",
        "2.1.3.02",
        "ICMS ST a Recolher",
        "liability_current",
    ),
    "tax_icms_st_receivable": (
        "1.1.3.1.04",
        "1.1.4.02",
        "ICMS ST s/ Estoque (Mercadorias)",
        "asset_current",
    ),
    "tax_pis_st_payable": (
        "2.1.7.1.05S",
        "2.1.3.01",
        "PIS ST a Recolher",
        "liability_current",
    ),  # ITG: Falls under Simples or generic tax payable
    "tax_pis_st_receivable": (
        "1.1.4.1.05S",
        "1.1.4.02",
        "PIS ST a Compensar",
        "asset_current",
    ),
    "tax_cofins_st_payable": (
        "2.1.7.1.04S",
        "2.1.3.01",
        "COFINS ST a Recolher",
        "liability_current",
    ),  # ITG: Falls under Simples or generic
    "tax_cofins_st_receivable": (
        "1.1.4.1.04S",
        "1.1.4.02",
        "COFINS ST a Compensar",
        "asset_current",
    ),
    "tax_issqn_payable": (
        "2.1.7.1.08",
        "2.1.3.03",
        "ISSQN a Recolher",
        "liability_current",
    ),
    "tax_issqn_receivable": (
        "1.1.4.1.09",
        "1.1.4.02",
        "ISSQN a Compensar",
        "asset_current",
    ),
    "tax_issqn_sales_revenue_contra": (
        "6.1.1.2.04",
        "3.1.1.04",
        "ISSQN sobre Serviços",
        "income_other",
    ),
    "tax_issqn_credit_note_revenue": (
        "6.1.1.2.24",
        "3.1.1.04",
        "ISSQN Devolução Serviços",
        "income_other",
    ),
    "tax_ii_payable": (
        "2.1.7.1.13",
        None,
        "II a Recolher",
        "liability_current",
    ),  # No direct ITG 1000 code for "II a Recolher" liability
    "tax_ii_receivable": ("1.1.4.1.10", "1.1.4.02", "II a Compensar", "asset_current"),
    "tax_ii_sales_revenue_contra": (
        "6.1.1.2.11",
        "3.1.1.04",
        "II sobre Vendas",
        "income_other",
    ),
    "tax_ii_credit_note_revenue": (
        "6.1.1.2.31",
        "3.1.1.04",
        "II Devolução Venda",
        "income_other",
    ),
    "tax_csll_payable": (
        "2.1.7.1.07",
        "3.2.5.01",
        "CSLL a Recolher",
        "liability_current",
    ),  # ITG uses expense for provision
    "tax_csll_receivable": (
        "1.1.4.1.07",
        "1.1.4.02",
        "CSLL a Compensar",
        "asset_current",
    ),
    "tax_csll_sales_revenue_contra": (
        "6.1.1.2.09",
        "3.1.1.04",
        "CSLL sobre Vendas",
        "income_other",
    ),
    "tax_csll_credit_note_revenue": (
        "6.1.1.2.29",
        "3.1.1.04",
        "CSLL Devolução Venda",
        "income_other",
    ),
    "tax_csll_wh_payable": (
        "2.1.7.1.07",
        "3.2.5.01",
        "CSLL Retido a Pagar (WH)",
        "liability_current",
    ),
    "tax_csll_wh_receivable": (
        "1.1.4.1.07",
        "1.1.4.02",
        "CSLL Retido a Compensar (WH)",
        "asset_current",
    ),
    "tax_irpj_payable": (
        "2.1.7.1.06",
        "3.2.5.02",
        "IRPJ a Recolher",
        "liability_current",
    ),  # ITG uses expense for provision
    "tax_irpj_receivable": (
        "1.1.4.1.06",
        "1.1.4.02",
        "IRPJ a Compensar",
        "asset_current",
    ),
    "tax_irpj_sales_revenue_contra": (
        "6.1.1.2.10",
        "3.1.1.04",
        "IRPJ sobre Vendas",
        "income_other",
    ),
    "tax_irpj_credit_note_revenue": (
        "6.1.1.2.30",
        "3.1.1.04",
        "IRPJ Devolução Venda",
        "income_other",
    ),
    "tax_irpj_wh_payable": (
        "2.1.7.1.06",
        "3.2.5.02",
        "IRPJ Retido a Pagar (WH)",
        "liability_current",
    ),
    "tax_irpj_wh_receivable": (
        "1.1.4.1.06",
        "1.1.4.02",
        "IRPJ Retido a Compensar (WH)",
        "asset_current",
    ),
    "tax_inss_payable": (
        "2.1.6.1.01",
        "2.1.4.03",
        "INSS a Recolher (Serv/Outros)",
        "liability_current",
    ),
    "tax_inss_receivable": (
        "1.1.4.1.11",
        "1.1.4.02",
        "INSS a Compensar (Serv/Outros)",
        "asset_current",
    ),
    "tax_inss_wh_payable": (
        "2.1.6.1.01",
        "2.1.4.03",
        "INSS Retido a Pagar (WH)",
        "liability_current",
    ),
    "tax_inss_wh_receivable": (
        "1.1.4.1.11",
        "1.1.4.02",
        "INSS Retido a Compensar (WH)",
        "asset_current",
    ),
    "tax_icms_fcp_payable": (
        "2.1.7.1.03FCP",
        "2.1.3.02",
        "ICMS FCP a Recolher",
        "liability_current",
    ),  # Map to general ICMS payable
    "tax_icms_fcp_receivable": (
        "1.1.4.1.02FCP",
        "1.1.4.02",
        "ICMS FCP a Compensar",
        "asset_current",
    ),
    "tax_icms_fcp_st_payable": (
        "2.1.7.1.11FCP",
        "2.1.3.02",
        "ICMS FCP ST a Recolher",
        "liability_current",
    ),
    "tax_icms_fcp_st_receivable": (
        "1.1.3.1.04FCP",
        "1.1.4.02",
        "ICMS FCP ST s/ Estoque",
        "asset_current",
    ),
}


# Maps tax template XMLID to keys for account XMLIDs from MINIMAL_TAX_ACCOUNTS
# Tuple: (inv_rep_acc_key, ref_rep_acc_key)
# These keys refer to the keys in MINIMAL_TAX_ACCOUNTS for account lookup.
DEFAULT_TAX_TEMPLATES_ACCOUNTS = {
    # Non-deductible, Non-withholdable
    "l10n_br_coa.tax_template_out_icms": ("tax_icms_payable", "tax_icms_receivable"),
    "l10n_br_coa.tax_template_in_icms": ("tax_icms_receivable", "tax_icms_payable"),
    "l10n_br_coa.tax_template_out_ipi": ("tax_ipi_payable", "tax_ipi_receivable"),
    "l10n_br_coa.tax_template_in_ipi": ("tax_ipi_receivable", "tax_ipi_payable"),
    "l10n_br_coa.tax_template_out_pis": ("tax_pis_payable", "tax_pis_receivable"),
    "l10n_br_coa.tax_template_in_pis": ("tax_pis_receivable", "tax_pis_payable"),
    "l10n_br_coa.tax_template_out_cofins": (
        "tax_cofins_payable",
        "tax_cofins_receivable",
    ),
    "l10n_br_coa.tax_template_in_cofins": (
        "tax_cofins_receivable",
        "tax_cofins_sales_revenue",
    ),
    # Deductible (account for tax line, account for refund tax line)
    "l10n_br_coa.tax_template_icms_out_deductible": (
        "tax_icms_sales_revenue",
        "tax_icms_purchase_expense",
    ),
    "l10n_br_coa.tax_template_icms_in_deductible": (
        "tax_icms_sales_revenue",
        "tax_icms_payable",
    ),
    "l10n_br_coa.tax_template_out_ipi_deductible": (
        "tax_ipi_sales_revenue",
        "tax_ipi_purchase_expense",
    ),
    "l10n_br_coa.tax_template_in_ipi_deductible": (
        "tax_ipi_sales_revenue",
        "tax_ipi_payable",
    ),
    "l10n_br_coa.tax_template_out_pis_deductible": (
        "tax_pis_sales_revenue",
        "tax_pis_purchase_expense",
    ),
    "l10n_br_coa.tax_template_in_pis_deductible": (
        "tax_pis_sales_revenue",
        "tax_pis_payable",
    ),
    "l10n_br_coa.tax_template_cofins_out_deductible": (
        "tax_cofins_sales_revenue",
        "tax_cofins_purchase_expense",
    ),
    "l10n_br_coa.tax_template_cofins_in_deductible": (
        "tax_cofins_sales_revenue",
        "tax_cofins_payable",
    ),
    # Withholding (WH)
    "l10n_br_coa.tax_template_out_pis_wh": (
        "tax_pis_receivable",
        "tax_pis_payable",
    ),  # Tax reduces receivable. Refund gives back to receivable.
    "l10n_br_coa.tax_template_in_pis_wh": ("tax_pis_payable", "tax_pis_receivable"),
    "l10n_br_coa.tax_template_out_cofins_wh": (
        "tax_cofins_receivable",
        "tax_cofins_payable",
    ),
    "l10n_br_coa.tax_template_in_cofins_wh": (
        "tax_cofins_payable",
        "tax_cofins_receivable",
    ),
    # TODO: Add CSLL_WH, IRPJ_WH, INSS_WH if needed
    # Simples Nacional
    "l10n_br_coa.tax_template_out_icmssn": (
        "tax_icmssn_payable",
        "tax_icms_receivable",
    ),
}


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
            tax_template = self.env.ref(tax_template_xmlid, raise_if_not_found=False)
            company_tax = self.env["account.tax"].search(
                [
                    ("name", "=", tax_template.name),
                    ("type_tax_use", "=", tax_template.type_tax_use),
                    ("company_id", "=", company.id),
                    ("tax_group_id.name", "=", tax_template.tax_group_id.name),
                ],
                limit=1,
            )

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
