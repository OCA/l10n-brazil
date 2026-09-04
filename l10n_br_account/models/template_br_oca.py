# Copyright 2019-TODAY Akretion - Renato Lima
# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(template_code, company, install_demo, force_create)
        if company.currency_id == self.env.ref("base.BRL"):
            self.load_fiscal_taxes([company])
        return result

    def _get_demo_data_move(self, company=False):
        """
        Set the l10n_latam_document_type_id on demo invoices for
        Brazilian companies.
        """
        move_data = super()._get_demo_data_move(company)
        if (
            "l10n_latam.document.type" in self.env
            and company.account_fiscal_country_id.code == "BR"
        ):
            # Find a default document type for Brazil
            # Use 'all' internal type as it matches all move types
            latam_doc_type = self.env["l10n_latam.document.type"].search(
                [
                    ("country_id", "=", company.account_fiscal_country_id.id),
                    ("internal_type", "=", "all"),
                    ("active", "=", True),
                ],
                limit=1,
                order="sequence,id",
            )
            if latam_doc_type:
                for move in move_data.values():
                    if move.get("move_type") in (
                        "out_invoice",
                        "out_refund",
                        "in_invoice",
                        "in_refund",
                    ):
                        move["l10n_latam_document_type_id"] = latam_doc_type.id
        return move_data

    def load_fiscal_taxes(self, companies=None):
        """
        Create missing account.tax for Brazil.
        Add missing account.account for the Brazilian taxes.
        Relate account taxes with fiscal taxes to enable the Brazilian
        tax engine to kick in with the installed chart of account.
        """
        _logger.info(f"load_fiscal_taxes called for companies: {companies}")
        tax_group_data = self._parse_csv(
            "br_oca", "account.tax.group", module="l10n_br_coa"
        )
        tax_group_data_rel = self._parse_csv(
            "br_oca", "account.tax.group", module="l10n_br_account"
        )
        tax_data = self._parse_csv("br_oca", "account.tax", module="l10n_br_coa")

        if companies is None:
            companies = self.env["res.company"].search(
                [("chart_template", "=", "br_oca")]
            )

        for company in companies:
            _logger.info(f"Processing company {company.name} (ID: {company.id})")
            for key, value in tax_group_data.items():
                id_key = f"{company.id}_{key}"
                existing_group = self.env.ref(
                    f"l10n_br_coa.{id_key}", raise_if_not_found=False
                ) or self.env.ref(f"account.{id_key}", raise_if_not_found=False)
                if existing_group:
                    if (
                        not existing_group.fiscal_tax_group_id
                        and key in tax_group_data_rel
                    ):
                        existing_group.fiscal_tax_group_id = self.env.ref(
                            tax_group_data_rel[key]["fiscal_tax_group_id"]
                        ).id
                    _logger.debug(f"Tax group {id_key} already exists")
                    continue

                else:
                    group_vals = {
                        "name": value["name"],
                        "company_id": company.id,
                    }
                    if key in tax_group_data_rel:
                        group_vals["fiscal_tax_group_id"] = self.env.ref(
                            tax_group_data_rel[key]["fiscal_tax_group_id"]
                        ).id

                    tax_group = self.env["account.tax.group"].create(group_vals)
                    self.env["ir.model.data"].create(
                        {
                            "name": id_key,
                            "module": "l10n_br_coa",
                            "model": "account.tax.group",
                            "res_id": tax_group.id,
                            "noupdate": True,
                        }
                    )
            for key, value in tax_data.items():
                id_key = f"{company.id}_{key}"
                existing_tax = self.env.ref(
                    f"l10n_br_coa.{id_key}", raise_if_not_found=False
                )
                if existing_tax:
                    continue
                existing_tax = self.env["account.tax"].search(
                    [
                        ("name", "=", value["name"]),
                        ("company_id", "=", company.id),
                    ],
                    limit=1,
                )
                if existing_tax:
                    # Ensure the XML ID mapping exists for this company/tax
                    self.env["ir.model.data"].create(
                        {
                            "name": id_key,
                            "module": "l10n_br_coa",
                            "model": "account.tax",
                            "res_id": existing_tax.id,
                            "noupdate": True,
                        }
                    )
                    _logger.debug(
                        "Tax %s for company %s already exists; XML ID %s created",
                        value["name"],
                        company.name,
                        id_key,
                    )
                else:
                    tax_vals = {
                        "name": value["name"],
                        "company_id": company.id,
                        "tax_group_id": self.env.ref(
                            f"l10n_br_coa.{company.id}_{value['tax_group_id']}"
                        ).id,
                        "type_tax_use": value["type_tax_use"],
                        "price_include": value["price_include"],
                        "deductible": value["deductible"],
                        "withholdable": value["withholdable"],
                    }

                    account_tax = self.env["account.tax"].create(tax_vals)
                    self.env["ir.model.data"].create(
                        {
                            "name": id_key,
                            "module": "l10n_br_coa",
                            "model": "account.tax",
                            "res_id": account_tax.id,
                            "noupdate": True,
                        }
                    )

            # Flush to ensure repartition lines are created by computed fields
            self.env.flush_all()

            tax_count = self.env["account.tax"].search_count(
                [("company_id", "=", company.id)]
            )
            _logger.info(f"Created {tax_count} taxes for company {company.name}")

            self.env["account.chart.template"]._populate_default_br_tax_accounts(
                company, flavor="cfc", review_suffix=".BR"
            )
