from . import models
from . import controllers

# from odoo.addons.payment.models.payment_provider import (
#     create_missing_journal_for_providers,
# )
from odoo.addons.payment import reset_payment_provider


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "bacenpix")
