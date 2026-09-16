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
    _rec_name = "c_cta"
    _order = "nivel_cta, c_cta"

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
    c_cta = fields.Char(
        string="Account",
        required=True,
        size=53,
        help="Official DeRE field cCta.",
    )
    c_cta_interna = fields.Char(
        string="Internal account",
        required=True,
        size=50,
        help="Official DeRE field cCtaInterna.",
    )
    c_dbr_mista = fields.Char(
        string="Mixed-account split",
        required=True,
        size=3,
        default="000",
        help="Official DeRE field cDbrMista.",
    )
    nome_cta = fields.Char(
        string="Account name",
        required=True,
        size=100,
        help="Official DeRE field nomeCta.",
    )
    ind_cta = fields.Selection(
        IND_CTA,
        string="Account type",
        required=True,
        help="Official DeRE field indCta.",
    )
    desc_cta = fields.Char(
        string="Description",
        size=600,
        help="Official DeRE field descCta.",
    )
    c_cta_sup = fields.Char(
        string="Parent account",
        size=53,
        help="Official DeRE field cCtaSup.",
    )
    c_cta_ref = fields.Char(
        string="Referential account",
        required=True,
        size=13,
        help="Official DeRE field cCtaRef.",
    )
    nivel_cta = fields.Integer(
        string="Level",
        required=True,
        default=1,
        help="Official DeRE field nivelCta.",
    )
    nat_cta = fields.Selection(
        NAT_CTA,
        string="Balance nature",
        required=True,
        help="Official DeRE field natCta.",
    )
    cod_nat = fields.Selection(
        COD_NAT,
        string="Nature",
        required=True,
        help="Official DeRE field codNat.",
    )
    tax_code_id = fields.Many2one(
        comodel_name="l10n_br_dere.tax.code",
        string="Taxation code",
        help="Official DeRE field codTrib.",
    )
    ind_trib_iss = fields.Selection(
        IND_TRIB_ISS,
        string="ISS indicator",
        help="Official DeRE field indTribISS.",
    )
    id_lei_disp = fields.Char(
        string="Legal-provision id",
        size=5,
        help="Official DeRE field idLeiDisp.",
    )
    ini_vig = fields.Date(
        string="Validity start",
        required=True,
        help="Official DeRE field iniVig.",
    )
    fim_vig = fields.Date(
        string="Validity end",
        help="Official DeRE field fimVig.",
    )

    def _to_xml_vals(self):
        self.ensure_one()
        return {
            "cCta": self.c_cta,
            "cCtaInterna": self.c_cta_interna,
            "cDbrMista": self.c_dbr_mista,
            "nomeCta": self.nome_cta,
            "indCta": self.ind_cta,
            "descCta": self.desc_cta,
            "cCtaSup": self.c_cta_sup,
            "cCtaRef": self.c_cta_ref,
            "nivelCta": self.nivel_cta,
            "natCta": self.nat_cta,
            "codNat": self.cod_nat,
            "codTrib": self.tax_code_id.code if self.tax_code_id else False,
            "indTribISS": self.ind_trib_iss,
            "idLeiDisp": self.id_lei_disp,
            "iniVig": fields.Date.to_string(self.ini_vig),
            "fimVig": fields.Date.to_string(self.fim_vig) if self.fim_vig else False,
        }
