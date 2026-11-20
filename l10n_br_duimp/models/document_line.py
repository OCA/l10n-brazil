# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    duimp_item_id = fields.Many2one(
        comodel_name="l10n_br_duimp.item",
        string="DUIMP Item",
        copy=False,
        help="DUIMP item that originated this fiscal document line. Used "
        "by l10n_br_duimp_nfe to build the nfe40_DI/adi tags.",
    )
