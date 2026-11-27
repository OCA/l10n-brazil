# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import api, models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    @api.depends("city_taxation_code_id")
    def _compute_issqn_fg_city_id(self):
        """Keep the incidence city parsed from an imported national NFS-e.

        The standard compute falls back to the company city when the line has
        no municipal taxation code. That city is not the ``cLocIncid`` of the
        note, so an imported national NFS-e keeps the value written from the XML.
        """
        imported = self.filtered(
            lambda line: line.document_id.imported_document
            and line.document_id._is_national_nfse_key()
        )
        return super(DocumentLine, self - imported)._compute_issqn_fg_city_id()

    @api.depends("product_id")
    def _compute_product_fiscal_fields(self):
        """The service of an imported national NFS-e stays the one of the file.

        Choosing the product of the review would copy its fiscal fields over the
        ones declared by the provider: a product registered as goods turns the line
        into ICMS and drops the taxes of the file from its list.
        """
        imported = self.filtered(
            lambda line: line.document_id.imported_document
            and line.document_id._is_national_nfse_key()
        )
        declared = {
            line: (line.tax_icms_or_issqn, line.service_type_id, line.nbs_id)
            for line in imported
        }
        result = super()._compute_product_fiscal_fields()
        for line, (domain, service_type, nbs) in declared.items():
            line.tax_icms_or_issqn = domain
            line.service_type_id = service_type
            line.nbs_id = nbs
        return result
