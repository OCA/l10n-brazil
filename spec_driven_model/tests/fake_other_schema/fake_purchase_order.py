# Copyright 2026 KMEE INFORMATICA LTDA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
from odoo import models


class PurchaseOrder(models.Model):
    """fake.purchase.order extended by a module of another schema, which then
    comes first in the MRO, like a fiscal document extended by several specs."""

    _inherit = "fake.purchase.order"
