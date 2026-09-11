# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import pytz

from odoo import _, fields, http
from odoo.http import request


class DfeDocumentBannerController(http.Controller):
    @http.route(
        [
            "/l10n_br_fiscal_dfe/document_banner",
            "/l10n_br_fiscal_dfe/document_banner/<string:fiscal_type>",
        ],
        auth="user",
        type="json",
    )
    def document_banner(self, fiscal_type="nfe", **kwargs):
        """Render the DF-e dashboard banner for a given fiscal document type.

        The company fields are looked up dynamically using the
        ``{fiscal_type}_*`` naming convention (e.g. ``nfe_last_nsu``), so the
        same banner works for NF-e, CT-e or any other DF-e service.
        """
        company = request.env.company
        DfeDocument = request.env["l10n_br_fiscal_dfe.document"]

        def typed(base, default=False):
            return getattr(company, f"{fiscal_type}_{base}", default)

        complete_dfe_docs = DfeDocument.search(
            [
                ("company_id", "=", company.id),
                ("fiscal_type", "=", fiscal_type),
                ("dfe_ids.document_type_dfe", "=", "complete"),
            ]
        )
        if complete_dfe_docs:
            FiscalDoc = request.env["l10n_br_fiscal.document"]
            imported_keys = set(
                FiscalDoc.search(
                    [
                        (
                            "document_key",
                            "in",
                            complete_dfe_docs.mapped("access_key"),
                        ),
                    ]
                ).mapped("document_key")
            )
            pending_import_count = len(
                complete_dfe_docs.filtered(
                    lambda doc: doc.access_key not in imported_keys
                )
            )
        else:
            pending_import_count = 0

        today = fields.Date.context_today(DfeDocument)
        today_domain = [
            ("company_id", "=", company.id),
            ("fiscal_type", "=", fiscal_type),
            ("create_date", ">=", today),
            ("is_own_document", "=", False),
        ]
        today_count = DfeDocument.search_count(today_domain)

        user_tz = pytz.timezone(request.env.user.tz or "UTC")
        last_query = typed("dfe_last_query")
        if last_query:
            last_query_str = (
                pytz.utc.localize(last_query)
                .astimezone(user_tz)
                .strftime("%d/%m/%Y %H:%M")
            )
        else:
            last_query_str = "-"

        next_query = typed("dfe_next_query")
        if next_query:
            next_query_str = (
                pytz.utc.localize(next_query)
                .astimezone(user_tz)
                .strftime("%d/%m/%Y %H:%M")
            )
        else:
            next_query_str = "-"

        last_nsu = typed("last_nsu")
        max_nsu = typed("max_nsu")
        nsu_synced = last_nsu and max_nsu and last_nsu >= max_nsu

        inactivity_warning = False
        inactivity_message = ""
        now = fields.Datetime.now()
        if last_query:
            inactivity_days = (now - last_query).days
            if inactivity_days > 30:
                inactivity_warning = True
                inactivity_message = _(
                    "Last DF-e query was %(days)s days ago. After 60 days of "
                    "inactivity, SEFAZ stops generating NSUs for this CNPJ "
                    "(no retroactive recovery).",
                    days=inactivity_days,
                )
        else:
            inactivity_warning = True
            inactivity_message = _(
                "DF-e distribution has never been queried. Configure and run "
                "the first query to start receiving documents."
            )

        dfe_nsu_action = request.env.ref(
            "l10n_br_fiscal_dfe.dfe_action", raise_if_not_found=False
        )
        dfe_log_action = request.env.ref(
            "l10n_br_fiscal_dfe.dfe_distribution_log_action",
            raise_if_not_found=False,
        )

        return {
            "html": request.env["ir.qweb"]._render(
                "l10n_br_fiscal_dfe.dfe_document_banner",
                {
                    "company": company,
                    "fiscal_type": fiscal_type,
                    "last_query_str": last_query_str,
                    "last_nsu": last_nsu or "0",
                    "max_nsu": max_nsu or "0",
                    "last_status": typed("dfe_last_status"),
                    "last_status_code": typed("dfe_last_status_code"),
                    "nsu_synced": nsu_synced,
                    "pending_import_count": pending_import_count,
                    "today_count": today_count,
                    "dfe_nsu_action_id": dfe_nsu_action.id if dfe_nsu_action else False,
                    "dfe_log_action_id": dfe_log_action.id if dfe_log_action else False,
                    "auto_fetch": typed("auto_fetch"),
                    "next_query_str": next_query_str,
                    "is_homologation": typed("environment") == "2",
                    "inactivity_warning": inactivity_warning,
                    "inactivity_message": inactivity_message,
                },
            )
        }
