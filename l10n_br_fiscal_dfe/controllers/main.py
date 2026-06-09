# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request


class DfeDocumentBannerController(http.Controller):
    @http.route("/l10n_br_fiscal_dfe/banner", type="json", auth="user")
    def document_banner(self, fiscal_type="nfe", **kwargs):
        """
        Generates the HTML for the DF-e Dashboard Banner dynamically
        based on whether the user is looking at NF-e or CT-e.
        """
        company = request.env.company

        # Dynamically fetch the fields based on fiscal type (nfe or cte)
        last_query = getattr(company, f"{fiscal_type}_dfe_last_query", False)
        next_query = getattr(company, f"{fiscal_type}_dfe_next_query", False)
        last_nsu = getattr(company, f"{fiscal_type}_last_nsu", "0")
        max_nsu = getattr(company, f"{fiscal_type}_max_nsu", "0")
        environment = getattr(company, f"{fiscal_type}_environment", "1")
        auto_fetch = getattr(company, f"{fiscal_type}_auto_fetch", False)

        # Count documents that have a 'complete' XML payload but aren't processed yet
        pending_count = request.env["l10n_br_fiscal_dfe.document"].search_count(
            [
                ("company_id", "=", company.id),
                ("fiscal_type", "=", fiscal_type),
                ("dfe_ids.document_type_dfe", "=", "complete"),
            ]
        )

        values = {
            "company": company,
            "fiscal_type": fiscal_type.upper(),
            "last_query": last_query,
            "next_query": next_query,
            "last_nsu": last_nsu,
            "max_nsu": max_nsu,
            "auto_fetch": auto_fetch,
            "is_homologation": environment == "2",
            "pending_count": pending_count,
        }

        return {
            "html": request.env["ir.qweb"]._render(
                "l10n_br_fiscal_dfe.dfe_banner_template", values
            )
        }
