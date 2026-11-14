# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# Copyright 2025 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = "account.payment.line.create"

    allow_error = fields.Boolean(
        string="Permitir linhas com erro na exportação, "
        "já incluidas em outras ordens",
    )

    allow_rejected = fields.Boolean(
        string="Permitir linhas com retorno rejeitado",
    )

    @api.depends("allow_error", "allow_rejected")
    def _compute_move_line_domain(self):
        res = super()._compute_move_line_domain()
        for wizard in self:
            # States that must always be skipped
            ignored_states = {
                "added",
                "added_paid",
                "exported",
                "accepted",
                "accepted_hml",
                "done",
            }

            # Optional skips, controlled by the wizard's check-boxes
            if not wizard.allow_error:
                ignored_states.add("exporting_error")
            if not wizard.allow_rejected:
                ignored_states.add("not_accepted")

            wizard.move_line_domain = list(wizard.move_line_domain or []) + [
                ("cnab_state", "not in", sorted(ignored_states))
            ]
        return res
