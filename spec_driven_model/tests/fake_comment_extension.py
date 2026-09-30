# Copyright 2026 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
from odoo import fields, models


class CommentExtension(models.AbstractModel):
    """Downstream extension of the *remaining* spec model poxsd.10.comment.

    poxsd.10.comment is never injected into a concrete Odoo model, so the
    _register_remaining_schema_models_hook turns it into a concrete model on
    its own. This class mirrors how a downstream module (e.g. l10n_br_account_nfe
    for nfe.40.detpag) adds a field to such a remaining model via _inherit. It is
    what makes the leaked synthesized class fatal on a registry rebuild (#4668).
    """

    _inherit = "poxsd.10.comment"

    poxsd10_extra = fields.Char(string="extra")
