# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class GnreGenerateWizard(models.TransientModel):
    """Gera as guias a partir das obrigações pendentes de um período.

    Este é o passo que a fatura não faz: postar a nota cria a obrigação, e a
    guia nasce aqui, do agrupamento. Sem essa separação não há como consolidar
    o mês, que é o caso normal de quem tem inscrição estadual no destino.
    """

    _name = "l10n_br_gnre.generate.wizard"
    _description = "Generate GNRE Guides"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    date_from = fields.Date(
        string="Vencimento de",
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1),
    )

    date_to = fields.Date(
        string="Vencimento até",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )

    fiscal_state_ids = fields.Many2many(
        comodel_name="res.country.state",
        string="UFs Favorecidas",
        help="Vazio significa todas as UFs com obrigação pendente no período.",
    )

    obligation_count = fields.Integer(
        string="Obrigações Pendentes",
        compute="_compute_preview",
    )

    guide_count = fields.Integer(
        string="Guias a Emitir",
        compute="_compute_preview",
    )

    def _obligation_domain(self):
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("state", "=", "pending"),
            ("date_due", ">=", self.date_from),
            ("date_due", "<=", self.date_to),
        ]
        if self.fiscal_state_ids:
            domain.append(("fiscal_state_id", "in", self.fiscal_state_ids.ids))
        return domain

    def _compute_preview(self):
        for wizard in self:
            obligations = self.env["l10n_br_gnre.obligation"].search(
                wizard._obligation_domain()
            )
            wizard.obligation_count = len(obligations)
            wizard.guide_count = len(obligations.group_for_guides())

    def action_generate(self):
        self.ensure_one()
        obligations = self.env["l10n_br_gnre.obligation"].search(
            self._obligation_domain()
        )
        if not obligations:
            raise UserError(_("Nenhuma obrigação pendente com vencimento no período."))

        batches = obligations.group_for_guides()
        guides = self.env["l10n_br_fiscal.document"]
        for batch in batches:
            guides |= self.env["l10n_br_fiscal.document"]._create_gnre_guide(batch)

        return {
            "type": "ir.actions.act_window",
            "name": _("Guias GNRE"),
            "res_model": "l10n_br_fiscal.document",
            "view_mode": "tree,form",
            "domain": [("id", "in", guides.ids)],
        }
