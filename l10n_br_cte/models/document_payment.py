# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import MODELO_FISCAL_CTE
from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _edi_get_installments(self):
        """Installments of the collection (cobr) declared by the CT-e."""
        self.ensure_one()
        if self.document_type != MODELO_FISCAL_CTE:
            return super()._edi_get_installments()
        declared = self.cte40_cobr.cte40_dup.filtered(
            lambda dup: dup.cte40_dVenc and dup.cte40_vDup
        ).sorted(lambda dup: (dup.cte40_dVenc, dup.cte40_nDup or ""))
        return [
            EdiInstallment(dup.cte40_nDup or "", dup.cte40_dVenc, dup.cte40_vDup)
            for dup in declared
        ]
