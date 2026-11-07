from . import controllers
from . import models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(cr, registry):
    setup_provider(cr, registry, "brbank")


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "brbank")
