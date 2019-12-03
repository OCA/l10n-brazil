# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class UomUom(models.Model):

    _name = "uom.uom"
    _inherit = [
        "uom.uom",
        "l10n_br_fiscal.data.abstract",
        "mail.thread",
        "mail.activity.mixin",
    ]

    code = fields.Char(size=6)
