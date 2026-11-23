# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _edi_get_lots(self):
        """Lots the document declares for the line, as a list of ``EdiLot``.

        The module of the type of the document reads them from its file (the
        ``rastro`` group of the NF-e); the base declares none. The modules that
        use them, stock for one, do not need to know the type of the document.
        """
        self.ensure_one()
        return []
