# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nBrFiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    # The DPS XSD only accepts digits (TSCodTribNac [0-9]{6});
    # l10n_br_nfse_nacional exports the masked national code. Scoped to
    # NotaControl companies, other companies keep the original behaviour.
    nfse10_cTribNac = fields.Char(related=None, compute="_compute_nfse10_ctribnac")
    # Goiania uses a 9-digit municipal code (e.g. 331630101) that the national
    # XSD (TSCodTribMun [0-9]{3}) rejects: left out of the serialization and
    # added back by the document when packing the DPS for NotaControl.
    nfse10_cTribMun = fields.Char(related=None, compute="_compute_nfse10_ctribmun")

    @api.depends("national_taxation_code_id", "company_id")
    def _compute_nfse10_ctribnac(self):
        for line in self:
            nat = line.national_taxation_code_id
            unmasked = line.company_id.nfse_notacontrol
            line.nfse10_cTribNac = (
                nat.code_unmasked if unmasked else nat.code
            ) or False

    @api.depends("city_taxation_code_id", "company_id")
    def _compute_nfse10_ctribmun(self):
        for line in self:
            code = line.city_taxation_code_id.code
            line.nfse10_cTribMun = (
                False if line.company_id.nfse_notacontrol else code or False
            )
