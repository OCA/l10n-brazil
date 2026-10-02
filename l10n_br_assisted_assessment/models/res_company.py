# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    assessment_calendar_id = fields.Many2one(
        comodel_name="resource.calendar",
        string="Assessment Calendar",
        help="Calendar used to find the last business day of the assessment "
        "deadline. It must hold the national, state and municipal holidays of "
        "the head office domicile.",
    )
    assessment_dere_subject = fields.Boolean(
        string="Subject to DeRE",
        help="Taxpayers required to file the DeRE receive the assisted "
        "assessment by the 20th instead of the 15th of the following month.",
    )
    assessment_tolerance = fields.Float(
        string="Reconciliation Tolerance",
        default=0.01,
        help="Absolute difference below which an assessment line is considered "
        "reconciled against the bookkeeping.",
    )

    def _assessment_cnpj_root(self):
        """Return the 8 digit CNPJ root the assessment is consolidated under.

        The assessment is consolidated per taxpayer, gathering every branch
        (LC 214/2025, art. 42), so the endpoints answer for the root and not for
        a single establishment.
        """
        self.ensure_one()
        vat = getattr(self.partner_id, "cnpj_cpf_stripped", "") or ""
        if not vat:
            vat = re.sub(r"[^0-9A-Z]", "", (self.vat or "").upper())
        return vat[:8]
