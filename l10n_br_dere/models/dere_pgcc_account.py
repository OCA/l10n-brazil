# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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

    table_period_id = fields.Many2one(
        comodel_name="l10n_br_dere.table.period",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="table_period_id.company_id", store=True, index=True
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Accounting account",
        ondelete="restrict",
    )
    group_id = fields.Many2one(
        comodel_name="account.group",
        string="Account group",
        ondelete="restrict",
    )
    account_name = fields.Char(
        compute="_compute_account_name",
        string="Chart account name",
        help="Accounting account or group name, translated for the current user.",
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
        string="Official taxation code",
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

    def _auto_init(self):
        """Drop leftover PGCC rows so table_period_id can become required."""
        cr = self.env.cr
        cr.execute("SELECT to_regclass('public.l10n_br_dere_pgcc_account')")
        if cr.fetchone()[0]:
            cr.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'l10n_br_dere_pgcc_account'
                  AND column_name = 'declaration_id'
                """
            )
            if cr.fetchone():
                cr.execute(
                    """
                    UPDATE l10n_br_dere_pgcc_account AS pgcc
                       SET table_period_id = declaration.table_period_id
                      FROM l10n_br_dere_declaration AS declaration
                     WHERE pgcc.declaration_id = declaration.id
                       AND pgcc.table_period_id IS NULL
                       AND declaration.table_period_id IS NOT NULL
                    """
                )
            cr.execute(
                """
                DELETE FROM l10n_br_dere_pgcc_account AS pgcc
                 WHERE pgcc.table_period_id IS NULL
                   AND NOT EXISTS (
                        SELECT 1 FROM l10n_br_dere_trial_line AS trial
                         WHERE trial.pgcc_account_id = pgcc.id
                   )
                   AND NOT EXISTS (
                        SELECT 1 FROM l10n_br_dere_reserve_line AS reserve
                         WHERE reserve.pgcc_account_id = pgcc.id
                   )
                """
            )
        return super()._auto_init()

    @api.depends_context("lang")
    @api.depends("account_id", "group_id")
    def _compute_account_name(self):
        for rec in self:
            source = rec.account_id or rec.group_id
            rec.account_name = source.name if source else False

    def _check_pgcc_locked(self):
        if self.env.context.get("dere_force_declaration_write"):
            return
        if any(
            period.state == "accepted" or period.tables_accepted()
            for period in self.table_period_id
        ):
            raise UserError(
                _(
                    "Accepted DeRE table periods cannot change the PGCC "
                    "snapshot. Create a new validity if the chart changed."
                )
            )
        if self.table_period_id.declaration_ids.filtered(
            lambda rec: rec.state == "closed"
        ):
            raise UserError(
                _(
                    "Closed DeRE declarations cannot be modified. "
                    "Reopen the period first."
                )
            )

    def write(self, vals):
        self._check_pgcc_locked()
        return super().write(vals)

    def unlink(self):
        self._check_pgcc_locked()
        return super().unlink()

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
