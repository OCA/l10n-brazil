# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import controllers
from . import models

from odoo.addons.payment import reset_payment_provider


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "bacenpix")
