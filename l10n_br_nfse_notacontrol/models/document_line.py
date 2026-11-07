# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nBrFiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    # The DPS XSD only accepts digits (TSCodTribNac [0-9]{6}, TSCodNBS
    # [0-9]{9}); l10n_br_nfse_nacional exports the masked code. Scoped to
    # NotaControl companies, other companies keep the original behaviour.
    nfse10_cTribNac = fields.Char(
        related=False, compute="_compute_nfse10_unmasked_codes"
    )
    nfse10_cNBS = fields.Char(related=False, compute="_compute_nfse10_unmasked_codes")

    @api.depends("national_taxation_code_id", "nbs_id", "company_id")
    def _compute_nfse10_unmasked_codes(self):
        for line in self:
            unmasked = line.company_id.nfse_notacontrol
            nat, nbs = line.national_taxation_code_id, line.nbs_id
            line.nfse10_cTribNac = (
                nat.code_unmasked if unmasked else nat.code
            ) or False
            line.nfse10_cNBS = (nbs.code_unmasked if unmasked else nbs.code) or False
