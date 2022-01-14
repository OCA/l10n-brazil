# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import models
from . import controllers

from odoo.addons.payment import reset_payment_provider


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "pagseguro")
