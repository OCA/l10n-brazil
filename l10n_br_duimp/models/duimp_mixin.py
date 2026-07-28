# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class L10nBrDuimpMixin(models.AbstractModel):
    _name = "l10n_br_duimp.mixin"
    _description = "DUIMP Mixin"

    def _s_currency(self, siscomex_code):
        """Resolve a res.currency by its Siscomex numeric code.

        Ported from ``l10n_br_di.mixin`` (KMEE 14.0): both the DI extract
        and the DUIMP payload identify currencies by the Siscomex code
        rather than the ISO name.
        """
        if not siscomex_code:
            return self.env["res.currency"]
        return self.env["res.currency"].search(
            [("siscomex_code", "=", str(siscomex_code).zfill(3))],
            limit=1,
        )
