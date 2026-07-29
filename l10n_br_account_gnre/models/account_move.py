# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Quais campos da linha fiscal alimentam cada origem de valor da regra por UF.
# Ler a linha FISCAL, e nao a linha de imposto contabil, e deliberado: o DIFAL
# nao gera account.move.line com tax_line_id proprio, entao um gatilho que
# varresse as linhas de imposto simplesmente nao o veria.
AMOUNT_FIELDS = {
    "icmsst": ("icmsst_value", "icmsfcpst_value"),
    "difal": ("icms_destination_value", "icmsfcp_value"),
}


class AccountMove(models.Model):
    _inherit = "account.move"

    gnre_obligation_ids = fields.One2many(
        comodel_name="l10n_br_gnre.obligation",
        inverse_name="move_id",
        string="Obrigações de GNRE",
        readonly=True,
    )

    gnre_obligation_count = fields.Integer(
        compute="_compute_gnre_obligation_count",
    )

    @api.depends("gnre_obligation_ids")
    def _compute_gnre_obligation_count(self):
        for move in self:
            move.gnre_obligation_count = len(move.gnre_obligation_ids)

    def action_view_gnre_obligations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Obrigações de GNRE"),
            "res_model": "l10n_br_gnre.obligation",
            "view_mode": "tree,form",
            "domain": [("move_id", "=", self.id)],
        }

    def _gnre_destination_state(self):
        """UF favorecida: onde a mercadoria entra, não onde a fatura é enviada."""
        self.ensure_one()
        partner = self.partner_shipping_id or self.partner_id
        return partner.state_id

    def _gnre_amounts_by_source(self):
        """Sum the fiscal line amounts per amount source of the rule.

        Returns {'icmsst': (principal, fcp), ...}, skipping what is zero.
        """
        self.ensure_one()
        totals = {}
        for source, (principal_field, fcp_field) in AMOUNT_FIELDS.items():
            principal = sum(
                self.fiscal_document_id.fiscal_line_ids.mapped(principal_field)
            )
            fcp = sum(self.fiscal_document_id.fiscal_line_ids.mapped(fcp_field))
            if principal or fcp:
                totals[source] = (principal, fcp)
        return totals

    def _gnre_eligible(self):
        """Only outgoing invoices with a fiscal document generate a guide."""
        self.ensure_one()
        return (
            self.move_type == "out_invoice"
            and self.fiscal_document_id
            and self.fiscal_document_id.document_type_id
        )

    def _create_gnre_obligations(self):
        """Create the pending obligations of every eligible invoice.

        The invoice creates the OBLIGATION, never the guide: the guide comes
        from grouping obligations later, which is what allows the monthly
        consolidation. See the wizard in l10n_br_gnre.
        """
        obligations = self.env["l10n_br_gnre.obligation"]
        for move in self.filtered(lambda m: m._gnre_eligible()):
            state = move._gnre_destination_state()
            if not state or state == move.company_id.state_id:
                continue
            for source, (principal, fcp) in move._gnre_amounts_by_source().items():
                config = self.env["l10n_br_gnre.state.config"]._find_config(
                    move.company_id, state, source
                )
                if not config:
                    continue
                values = self.env["l10n_br_gnre.obligation"]._prepare_from_document(
                    move.fiscal_document_id,
                    config,
                    {
                        "move_id": move.id,
                        "amount_principal": principal,
                        "amount_fcp": fcp,
                        "authority_partner_id": config._gnre_authority(move).id,
                    },
                )
                obligations |= obligations.create(values)
        return obligations

    def _gnre_undo_obligations(self):
        """Drop the pending obligations when the invoice goes back to draft.

        An obligation already consumed by a transmitted guide is not dropped:
        the money is owed to the state, so the way back is a correction, not a
        silent delete.
        """
        for move in self:
            obligations = move.gnre_obligation_ids
            blocked = obligations.filtered(lambda o: o.state in ("transmitted", "paid"))
            if blocked:
                raise UserError(
                    _(
                        "A fatura %(move)s não pode voltar para rascunho: a "
                        "GNRE %(guide)s já foi transmitida.",
                        move=move.display_name,
                        guide=", ".join(blocked.mapped("guide_id.display_name")),
                    )
                )
            obligations.filtered(lambda o: o.state == "grouped").write(
                {"guide_id": False, "state": "pending"}
            )
            obligations.unlink()

    def _post(self, soft=True):
        posted = super()._post(soft)
        posted._create_gnre_obligations()
        return posted

    def button_draft(self):
        self._gnre_undo_obligations()
        return super().button_draft()
