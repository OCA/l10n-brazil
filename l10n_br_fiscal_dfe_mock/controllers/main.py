# Copyright 2026 Engenere (<https://engenere.one>)
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo.http import request

from odoo.addons.l10n_br_fiscal_dfe.controllers.main import (
    DfeDocumentBannerController,
)


class DfeDocumentBannerControllerMock(DfeDocumentBannerController):
    def document_banner(self):
        result = super().document_banner()
        company = request.env.company
        if company.dfe_mock_mode:
            mock_banner = request.env["ir.qweb"]._render(
                "l10n_br_fiscal_dfe_mock.dfe_mock_banner_warning", {}
            )
            result["html"] = mock_banner + result["html"]
        return result
