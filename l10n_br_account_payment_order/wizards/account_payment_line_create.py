# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
#   @author Daniel Sadamo <daniel.sadamo@kmee.com.br>
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# Copyright 2025 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = "account.payment.line.create"

    allow_error = fields.Boolean(
        string="Permitir linhas com erro na exportação, "
        "já incluidas em outras ordens",
    )

    allow_rejected = fields.Boolean(
        string="Permitir linhas com retorno rejeitado",
    )

    def _prepare_move_line_domain(self):
        domain = super()._prepare_move_line_domain()

        # States that must always be skipped
        ignored_states = {
            "added",
            "added_paid",
            "exported",
            "accepted",
            "accepted_hml",
            "done",
        }

        # Optional skips, controlled by the wizard’s check‑boxes
        if not self.allow_error:
            ignored_states.add("exporting_error")
        if not self.allow_rejected:
            ignored_states.add("not_accepted")

        domain.append(("cnab_state", "not in", list(ignored_states)))
        return domain
