# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import (
    COD_NAT,
    IND_CTA,
    IND_TRIB_ISS,
    NAT_CTA,
)


class DerePgccAccount(models.Model):
    _name = "l10n_br_dere.pgcc.account"
    _description = "DeRE PGCC snapshot account"
    _inherit = "dere.12.infoconta"
    _rec_name = "dere12_cCta"
    _order = "dere12_nivelCta, dere12_cCta"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_dere.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="declaration_id.company_id", store=True, index=True
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Accounting account",
        ondelete="restrict",
    )
    tax_code_id = fields.Many2one(
        comodel_name="l10n_br_dere.tax.code",
        string="Taxation code",
        help="Official DeRE field codTrib.",
    )
    dere12_cCta = fields.Char(
        string="Account",
        required=True,
        size=53,
        help="Official DeRE field cCta.",
    )
    dere12_cCtaInterna = fields.Char(
        string="Internal account",
        required=True,
        size=50,
        help="Official DeRE field cCtaInterna.",
    )
    dere12_cDbrMista = fields.Char(
        string="Mixed-account split",
        required=True,
        size=3,
        default="000",
        help="Official DeRE field cDbrMista.",
    )
    dere12_nomeCta = fields.Char(
        string="Account name",
        required=True,
        size=100,
        help="Official DeRE field nomeCta.",
    )
    dere12_indCta = fields.Selection(
        IND_CTA,
        string="Account type",
        required=True,
        help="Official DeRE field indCta.",
    )
    dere12_descCta = fields.Char(
        string="Description",
        size=600,
        help="Official DeRE field descCta.",
    )
    dere12_cCtaSup = fields.Char(
        string="Parent account",
        size=53,
        help="Official DeRE field cCtaSup.",
    )
    dere12_cCtaRef = fields.Char(
        string="Referential account",
        required=True,
        size=13,
        help="Official DeRE field cCtaRef.",
    )
    dere12_nivelCta = fields.Integer(
        string="Level",
        required=True,
        default=1,
        help="Official DeRE field nivelCta.",
    )
    dere12_natCta = fields.Selection(
        NAT_CTA,
        string="Balance nature",
        required=True,
        help="Official DeRE field natCta.",
    )
    dere12_codNat = fields.Selection(
        COD_NAT,
        string="Nature",
        required=True,
        help="Official DeRE field codNat.",
    )
    dere12_codTrib = fields.Char(
        related="tax_code_id.code",
        store=True,
        string="Taxation code",
        help="Official DeRE field codTrib.",
    )
    dere12_indTribISS = fields.Selection(
        IND_TRIB_ISS,
        string="ISS indicator",
        help="Official DeRE field indTribISS.",
    )
    dere12_idLeiDisp = fields.Char(
        string="Legal-provision id",
        size=5,
        help="Official DeRE field idLeiDisp.",
    )
    dere12_iniVig = fields.Date(
        string="Validity start",
        required=True,
        help="Official DeRE field iniVig.",
    )
    dere12_fimVig = fields.Date(
        string="Validity end",
        help="Official DeRE field fimVig.",
    )

    def _to_xml_vals(self):
        self.ensure_one()
        return {
            "cCta": self.dere12_cCta,
            "cCtaInterna": self.dere12_cCtaInterna,
            "cDbrMista": self.dere12_cDbrMista,
            "nomeCta": self.dere12_nomeCta,
            "indCta": self.dere12_indCta,
            "descCta": self.dere12_descCta,
            "cCtaSup": self.dere12_cCtaSup,
            "cCtaRef": self.dere12_cCtaRef,
            "nivelCta": self.dere12_nivelCta,
            "natCta": self.dere12_natCta,
            "codNat": self.dere12_codNat,
            "codTrib": self.dere12_codTrib,
            "indTribISS": self.dere12_indTribISS,
            "idLeiDisp": self.dere12_idLeiDisp,
            "iniVig": fields.Date.to_string(self.dere12_iniVig),
            "fimVig": fields.Date.to_string(self.dere12_fimVig)
            if self.dere12_fimVig
            else False,
        }
