# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class UoMCategory(models.Model):

    _inherit = "uom.category"

    measure_type = fields.Selection(selection_add=[("area", "Àrea / Superfície")])
